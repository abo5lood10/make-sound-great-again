"""نقطة تشغيل البرنامج.

ويندوز وماك: برنامج بنافذة مستقلة (pywebview) فقط، ما يفتح المتصفح أبدًا (إلا لو طلبت --browser).
Linux: نافذة مستقلة (GTK + WebKit2)، والمتصفح كحل أخير لو ما فيه نافذة.
"""
import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from . import core, server
from .version import APP_NAME, VERSION

DESKTOP_ONLY = core.IS_WIN or core.IS_MAC  # هذي الأنظمة: نافذة برنامج، بدون متصفح


def already_running():
    """لو فيه نسخة شغّالة، نرجع (رابطها، وضعها، منفذها، إصدارها)."""
    for port in range(server.BASE_PORT, server.BASE_PORT + 20):
        try:
            with urllib.request.urlopen(f"http://{server.HOST}:{port}/api/ping", timeout=0.4) as r:
                data = json.loads(r.read())
                if data.get("app") == APP_NAME:
                    return f"http://{server.HOST}:{port}", data.get("mode"), port, data.get("version")
        except Exception:
            continue
    return None


def quit_existing(port):
    """نسخة قديمة شغّالة (إصدار مختلف أو وضع متصفح): نقفلها عشان تفتح الجديدة بدالها."""
    try:
        req = urllib.request.Request(f"http://{server.HOST}:{port}/api/quit", data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2).read()
    except Exception:
        return False
    for _ in range(20):
        time.sleep(0.2)
        if not already_running():
            return True
    return False


def show_error(text):
    """رسالة خطأ بنافذة (النسخة المجمّعة ما لها طرفية، فلازم المستخدم يشوف السبب)."""
    print(text, file=sys.stderr, flush=True)
    try:
        if core.IS_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, APP_NAME, 0x10)
        elif core.IS_MAC:
            safe = text.replace("\\", " ").replace('"', "'")
            subprocess.run(["osascript", "-e", f'display dialog "{safe}" with title "{APP_NAME}" '
                            'buttons {"OK"} default button "OK" with icon stop'], timeout=120)
    except Exception:
        pass


def pick_window_runner():
    """يرجع دالة تفتح نافذة مستقلة (تنتظر لين تنقفل)، أو None لو ما فيه طريقة على هذا الجهاز."""
    icon = str(core.ROOT / "assets" / "icon.png")
    if sys.platform.startswith("linux"):
        from . import window
        if window.available():
            return lambda url: window.open_window(url, APP_NAME, icon)
        return None
    try:
        import webview  # pywebview (ويندوز / ماك): خفيفة، تستخدم محرك العرض الموجود في النظام
    except ImportError:
        return None

    def run(url):
        webview.create_window(APP_NAME, url, width=720, height=900, min_size=(520, 600))
        webview.start()
    return run


def selftest():
    """يفتح النافذة فعليًا، ينتظر تحميل الصفحة، ثم يقفل. للفحص الآلي على ويندوز وماك (exit 0 = نجح)."""
    import webview
    httpd = server.make_server("window")
    url = f"http://{server.HOST}:{server.STATE.port}"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    win = webview.create_window(APP_NAME, url, width=720, height=900)
    ok = []

    def probe():
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                if win.evaluate_js("document.getElementById('go') !== null && document.title") == APP_NAME:
                    ok.append(True)
                    break
            except Exception:
                pass
            time.sleep(1)
        win.destroy()

    webview.start(probe)
    httpd.shutdown()
    print("window selftest:", "OK" if ok else "FAILED", flush=True)
    sys.exit(0 if ok else 1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="run.py", description=APP_NAME)
    ap.add_argument("--browser", action="store_true", help="افتح في المتصفح بدل نافذة مستقلة")
    ap.add_argument("--no-open", action="store_true", help="شغّل الخادم فقط بدون فتح أي شي")
    ap.add_argument("--selftest", action="store_true", help="فحص آلي: يفتح النافذة ويقفلها")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return

    runner = None
    if not args.browser and not args.no_open:
        runner = pick_window_runner()
        if runner is None and DESKTOP_ONLY:
            show_error("The app window couldn't start: the 'pywebview' package is missing.\n\n"
                       "If you started it from the source code, run:\n"
                       "pip install -r requirements.txt\n\n"
                       "Easier: download the ready-made Windows build (.exe) from the project's Releases page.")
            sys.exit(1)
    window_mode = runner is not None

    existing = already_running()
    stale = existing and (existing[3] != VERSION or (window_mode and existing[1] == "browser"))
    if stale and quit_existing(existing[2]):
        existing = None  # نسخة قديمة: قفلناها ونفتح الجديدة
    if existing:
        if args.browser:
            webbrowser.open(existing[0])
        print(f"{APP_NAME} is already running: {existing[0]}")
        return

    httpd = server.make_server("window" if window_mode else "browser")
    url = f"http://{server.HOST}:{server.STATE.port}"
    print(f"{APP_NAME} → {url}", flush=True)
    core.config_dir()

    if window_mode:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            runner(url)
            httpd.shutdown()
            return
        except Exception as e:
            if DESKTOP_ONLY:  # ويندوز / ماك: ما نرجع للمتصفح، نوضّح المشكلة
                httpd.shutdown()
                show_error(f"The app window couldn't start: {e}")
                sys.exit(1)
            print(f"(window unavailable: {e}) falling back to the browser", flush=True)
            server.STATE.mode = "browser"
            webbrowser.open(url)
            httpd.serve_forever()
            return

    threading.Thread(target=server.idle_watchdog, daemon=True).start()
    if not args.no_open:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
