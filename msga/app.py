"""نقطة تشغيل البرنامج: نافذة مستقلة (لو pywebview مثبّتة) أو المتصفح الافتراضي."""
import argparse
import threading
import urllib.request
import webbrowser

from . import core, server
from .version import APP_NAME


def already_running():
    """لو فيه نسخة شغّالة، نرجع رابطها بدل ما نفتح نسخة ثانية."""
    for port in range(server.BASE_PORT, server.BASE_PORT + 20):
        try:
            with urllib.request.urlopen(f"http://{server.HOST}:{port}/api/ping", timeout=0.4) as r:
                if APP_NAME.encode() in r.read():
                    return f"http://{server.HOST}:{port}"
        except Exception:
            continue
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="run.py", description=APP_NAME)
    ap.add_argument("--browser", action="store_true", help="افتح في المتصفح بدل نافذة مستقلة")
    ap.add_argument("--no-open", action="store_true", help="شغّل الخادم فقط بدون فتح أي شي")
    args = ap.parse_args(argv)

    existing = already_running()
    if existing:
        if not args.no_open:
            webbrowser.open(existing)
        print(f"{APP_NAME} is already running: {existing}")
        return

    window_mode = False
    webview = None
    if not args.browser and not args.no_open:
        try:
            import webview  # pywebview: خفيفة، تستخدم محرك العرض الموجود في النظام
            window_mode = True
        except ImportError:
            webview = None

    httpd = server.make_server("window" if window_mode else "browser")
    url = f"http://{server.HOST}:{server.STATE.port}"
    print(f"{APP_NAME} → {url}", flush=True)
    core.config_dir()

    if window_mode:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            webview.create_window(APP_NAME, url, width=720, height=900, min_size=(520, 600))
            webview.start()
            httpd.shutdown()
            return
        except Exception as e:  # ما فيه محرك عرض مناسب: نكمل بالمتصفح
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
