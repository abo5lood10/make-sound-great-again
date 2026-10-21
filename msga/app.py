"""نقطة تشغيل البرنامج.

ويندوز وماك: برنامج بنافذة مستقلة (pywebview) فقط، ما يفتح المتصفح أبدًا (إلا لو طلبت --browser).
Linux: نافذة مستقلة (GTK + WebKit2)، والمتصفح كحل أخير لو ما فيه نافذة.
"""
import argparse
import os
import json
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from . import core, server, winctl
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
    """يرجع دالة تفتح نافذة مستقلة (تنتظر لين تنقفل)، أو None لو ما فيه طريقة على هذا الجهاز.
    الدالة تاخذ (url, geometry) حيث geometry = (w, h, x, y, on_top) أو None للحجم العادي."""
    icon = str(core.ROOT / "assets" / "icon.png")
    if sys.platform.startswith("linux"):
        from . import window
        if window.available():
            def run_gtk(url, geo=None):
                if geo:
                    w, h, x, y, top = geo
                    return window.open_window(url, APP_NAME, icon, w, h, x, y, top)
                return window.open_window(url, APP_NAME, icon)
            return run_gtk
        return None
    try:
        import webview  # pywebview (ويندوز / ماك): خفيفة، تستخدم محرك العرض الموجود في النظام
    except ImportError:
        return None

    def run(url, geo=None):
        kw = dict(width=720, height=900, min_size=(360, 200))
        if geo:
            w, h, x, y, top = geo
            kw.update(width=w, height=h, x=x, y=y, on_top=top)
        win = webview.create_window(APP_NAME, url, **kw)
        winctl.register(win, "pywebview")
        from . import desktop
        webview.start(lambda: desktop.attach(win))
    return run


def setup_streams():
    """ويندوز: الطرفية cp1252 ما تقدر تطبع كل الحروف، والنسخة المجمّعة (بدون طرفية) ما لها stdout أصلًا.
    نخلي الطباعة UTF-8 ما تنهار، ونكتب السجل في ملف app.log (مفيد لو صار عطل)."""
    log = None
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if stream is None:
            if log is None:
                path = core.config_dir() / "app.log"
                try:
                    if path.exists() and path.stat().st_size > 1_000_000:
                        path.unlink()
                except OSError:
                    pass
                log = open(path, "a", encoding="utf-8", errors="replace", buffering=1)
            setattr(sys, name, log)
        else:
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass

    def hook(exc_type, exc, tb):
        import traceback
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        print(text, file=sys.stderr, flush=True)
        if getattr(sys, "frozen", False):
            show_error(f"{APP_NAME} crashed.\n\n{exc_type.__name__}: {exc}\n\nDetails: {core.config_dir() / 'app.log'}")

    sys.excepthook = hook


def selftest():
    """يفتح النافذة فعليًا، ينتظر تحميل الصفحة، ثم يقفل. للفحص الآلي على ويندوز وماك (exit 0 = نجح)."""
    import webview
    httpd = server.make_server("window")
    url = f"http://{server.HOST}:{server.STATE.port}"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    win = webview.create_window(APP_NAME, url, width=720, height=900)
    winctl.register(win, "pywebview")
    ok = []

    def probe():
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                if win.evaluate_js("document.getElementById('go') !== null && document.title") == APP_NAME:
                    ok.append("page")
                    break
            except Exception:
                pass
            time.sleep(1)
        if ok and core.IS_WIN:  # أيقونة جنب الساعة + أزرار الوسائط (نضغط «التالي» برمجيًا ونتأكد إنه وصل)
            try:
                from . import desktop
                tray = desktop.start_tray(lambda name: None)
                if tray:
                    ok.append("tray")
                    tray.stop()
                got = threading.Event()
                _, keys = desktop.start_media_keys(lambda name: got.set() if name == "next" else None)
                if "next" in keys:
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(0xB0, 0, 2, 0)
                    if got.wait(5):
                        ok.append("keys")
                print(f"tray/keys: {ok} registered={keys}", flush=True)
            except Exception as e:
                print("tray/keys failed:", e, flush=True)
        if ok:  # وضع المشغّل المصغّر: النافذة تتصغّر لمستطيل ثم ترجع
            try:
                winctl.set_mode("mini")
                time.sleep(1.5)
                mini = (win.width, win.height)
                winctl.set_mode("full")
                time.sleep(1.5)
                full = (win.width, win.height)
                print(f"mini window: {mini}, restored: {full}", flush=True)
                if 380 <= mini[0] <= 600 and mini[1] < 400 and full[0] > mini[0]:
                    ok.append("mini")
            except Exception as e:
                print("mini mode failed:", e, flush=True)
        win.destroy()

    webview.start(probe)
    httpd.shutdown()
    passed = ok == (["page", "tray", "keys", "mini"] if core.IS_WIN else ["page", "mini"])
    print("window selftest:", "OK" if passed else f"FAILED {ok}", flush=True)
    os._exit(0 if passed else 1)   # نطلع فورًا حتى لو بقي خيط (أيقونة / أزرار الوسائط)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="run.py", description=APP_NAME)
    ap.add_argument("--browser", action="store_true", help="افتح في المتصفح بدل نافذة مستقلة")
    ap.add_argument("--no-open", action="store_true", help="شغّل الخادم فقط بدون فتح أي شي")
    ap.add_argument("--selftest", action="store_true", help="فحص آلي: يفتح النافذة ويقفلها")
    args = ap.parse_args(argv)
    setup_streams()

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
    print(f"{APP_NAME} -> {url}", flush=True)
    core.config_dir()

    if window_mode:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        geo = None
        cfg = core.load_config()
        if cfg.get("start_player"):  # المستخدم اختار: البرنامج يفتح مباشرة بوضع المشغّل المصغّر
            w, h, x, y = winctl.mini_geometry(cfg.get("mini_corner", "bottom"))
            geo = (w, h, x, y, True)
            winctl.start_in_mini()
            url += "/?view=player"
        try:
            runner(url, geo)
            httpd.shutdown()
            # النافذة انقفلت: نطلع بالكامل (خيوط الأيقونة وأزرار الوسائط ما تخلي البرنامج معلّق بالخلفية)
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(0)
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
