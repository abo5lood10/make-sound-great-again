"""نقطة تشغيل البرنامج: نافذة مستقلة (GTK+WebKit2 على Linux، وpywebview على ويندوز وماك) أو المتصفح كحل أخير."""
import argparse
import json
import sys
import threading
import time
import urllib.request
import webbrowser

from . import core, server
from .version import APP_NAME


def already_running():
    """لو فيه نسخة شغّالة، نرجع (رابطها، وضعها) بدل ما نفتح نسخة ثانية."""
    for port in range(server.BASE_PORT, server.BASE_PORT + 20):
        try:
            with urllib.request.urlopen(f"http://{server.HOST}:{port}/api/ping", timeout=0.4) as r:
                data = json.loads(r.read())
                if data.get("app") == APP_NAME:
                    return f"http://{server.HOST}:{port}", data.get("mode"), port
        except Exception:
            continue
    return None


def quit_existing(port):
    """نسخة قديمة شغّالة بوضع المتصفح: نقفلها عشان تفتح نافذة مستقلة بدالها."""
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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="run.py", description=APP_NAME)
    ap.add_argument("--browser", action="store_true", help="افتح في المتصفح بدل نافذة مستقلة")
    ap.add_argument("--no-open", action="store_true", help="شغّل الخادم فقط بدون فتح أي شي")
    args = ap.parse_args(argv)

    window_mode = False
    runner = None
    if not args.browser and not args.no_open:
        runner = pick_window_runner()
        window_mode = runner is not None

    existing = already_running()
    if existing and window_mode and existing[1] == "browser" and quit_existing(existing[2]):
        existing = None  # قفلنا النسخة القديمة (وضع المتصفح) ونفتح نافذة
    if existing:
        if not args.no_open:
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
        except Exception as e:  # ما اشتغلت النافذة: نكمل بالمتصفح
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
