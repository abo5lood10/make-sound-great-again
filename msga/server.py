"""خادم محلي خفيف (مكتبة بايثون القياسية فقط) يقدّم الواجهة والـ API. يستمع على 127.0.0.1 فقط."""
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import core, updater
from .version import APP_NAME, VERSION

HOST = "127.0.0.1"
BASE_PORT = 8765
MAX_UPLOAD = 2 * 1024 * 1024 * 1024  # 2GB
IDLE_EXIT_SECONDS = 600  # في وضع المتصفح: لو ما فيه صفحة مفتوحة ولا مهام، يقفل نفسه (خفيف على الجهاز)

mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")


class State:
    """حالة التطبيق في الذاكرة: قائمة المهام + منفّذ المعالجة."""

    def __init__(self, mode="browser"):
        self.mode = mode
        self.items = []
        self.lock = threading.Lock()
        self.executor = None
        self.executor_jobs = 0
        self.last_seen = time.time()
        self.port = BASE_PORT
        self.thmanyah = None
        self.httpd = None

    def get_executor(self, jobs):
        if self.executor is None or jobs != self.executor_jobs:
            if self.executor:
                self.executor.shutdown(wait=False)  # اللي بالطابور يكمل، والجديد يروح للتنفيذ الجديد
            self.executor = ThreadPoolExecutor(jobs)
            self.executor_jobs = jobs
        return self.executor

    def new_item(self, label, kind):
        it = {"id": uuid.uuid4().hex[:10], "label": label, "kind": kind, "status": "waiting",
              "stage_key": None, "pct": 0, "error": None, "result": None}
        with self.lock:
            self.items.append(it)
        return it

    def busy(self):
        return any(i["status"] in ("waiting", "running") for i in self.items)


STATE = State()


def file_url(path):
    return "/files/" + quote(Path(path).name)


def error_dict(e):
    if isinstance(e, core.EnhanceError):
        return {"key": e.key, "params": e.params}
    return {"key": None, "text": str(e)}


def run_item(it, source, opts):
    def cb(stage, frac):
        it.update(stage_key=stage, pct=round(frac * 100))

    it["status"] = "running"
    try:
        res = core.process_item(source, opts, cb)
        r = res["report"]
        r.update(title=res["title"], output_url=file_url(res["output"]),
                 original_url=file_url(res["original"]) if res["original"] else None,
                 output_name=Path(res["output"]).name)
        it.update(status="done", stage_key="st_done", pct=100, result=r)
    except core.EnhanceError as e:
        it.update(status="error", error=error_dict(e))
    except Exception as e:  # خطأ غير متوقع: نعرضه بدل ما تنهار الواجهة
        it.update(status="error", error=error_dict(e))
    finally:
        if opts.get("cleanup_source"):
            try:
                Path(source).unlink()
            except OSError:
                pass


def run_playlist(it, url, opts, jobs):
    it.update(status="running", stage_key="reading_playlist")
    try:
        urls = core.expand_playlist(url)
    except core.EnhanceError as e:
        it.update(status="error", error=error_dict(e))
        return
    with STATE.lock:
        if it in STATE.items:
            STATE.items.remove(it)
    for u in urls:
        child = STATE.new_item(u, "url")
        STATE.get_executor(jobs).submit(run_item, child, u, dict(opts))


def open_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    if core.IS_WIN:
        os.startfile(str(path))  # noqa: S606
    elif core.IS_MAC:
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class Handler(BaseHTTPRequestHandler):
    server_version = "MSGA"

    def log_message(self, *a):
        pass

    # ---- أمان: localhost فقط + منع طلبات المواقع الثانية ----
    def _allowed_hosts(self):
        return {f"{HOST}:{STATE.port}", f"localhost:{STATE.port}"}

    def _guard(self):
        STATE.last_seen = time.time()
        if self.headers.get("Host", "") not in self._allowed_hosts():
            self.send_error(403)
            return False
        origin = self.headers.get("Origin")
        if self.command == "POST" and origin and urlparse(origin).netloc not in self._allowed_hosts():
            self.send_error(403)
            return False
        return True

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    # ---- GET ----
    def do_GET(self):
        if not self._guard():
            return
        path = urlparse(self.path).path
        if path == "/":
            self._serve_file(core.WEB_DIR, "index.html", cache=False)
        elif path.startswith("/static/"):
            self._serve_file(core.WEB_DIR, unquote(path[8:]))
        elif path.startswith("/files/"):
            self._serve_file(Path(core.load_config()["out"]), unquote(path[7:]), cache=False)
        elif path == "/api/ping":
            self._json({"ok": True, "app": APP_NAME})
        elif path == "/api/messages":
            self._json(core.MESSAGES)
        elif path == "/api/state":
            self._json(self._state())
        else:
            self.send_error(404)

    def _state(self):
        if STATE.thmanyah is None:
            STATE.thmanyah = core.find_thmanyah()
        with STATE.lock:
            items = [dict(i) for i in STATE.items]
        return {"app": APP_NAME, "version": VERSION, "mode": STATE.mode, "config": core.load_config(),
                "items": items, "presets": list(core.PRESETS), "thmanyah": STATE.thmanyah,
                "missing": core.missing_tools(need_download=True), "repo_url": updater.repo_url(),
                "platform": sys.platform}

    # ---- POST ----
    def do_POST(self):
        if not self._guard():
            return
        url = urlparse(self.path)
        path = url.path
        if path == "/api/submit":
            self._submit(self._read_json())
        elif path == "/api/upload":
            self._upload(parse_qs(url.query))
        elif path == "/api/config":
            core.save_config({**core.load_config(), **self._read_json()})
            self._json({"config": core.load_config()})
        elif path == "/api/clear":
            with STATE.lock:
                STATE.items[:] = [i for i in STATE.items if i["status"] in ("waiting", "running")]
            self._json({"ok": True})
        elif path == "/api/clean":
            try:
                days = max(0, int(self._read_json().get("days", 30)))
            except (TypeError, ValueError):
                days = 30
            self._json({"deleted": core.clean_old(core.load_config()["out"], days)})
        elif path == "/api/open":
            open_folder(core.load_config()["out"])
            self._json({"ok": True})
        elif path == "/api/update/check":
            self._json(updater.check())
        elif path == "/api/update/apply":
            self._json(updater.apply())
        elif path == "/api/update/ytdlp":
            self._json(updater.update_ytdlp())
        elif path == "/api/ytdlp/version":
            self._json({"version": updater.ytdlp_version()})
        elif path == "/api/restart":
            self._json({"ok": True})
            threading.Thread(target=restart_app, daemon=True).start()
        elif path == "/api/quit":
            self._json({"ok": True})
            threading.Thread(target=stop_server, daemon=True).start()
        else:
            self.send_error(404)

    def _opts(self, d):
        cfg = core.load_config()
        preset = d.get("preset", cfg["preset"])
        fmt = d.get("format", cfg["format"])
        if preset not in (*core.PRESETS, "auto") or fmt not in core.CODECS:
            return None
        return {"preset": preset, "format": fmt, "out_dir": cfg["out"], "light": cfg["light"]}, cfg["jobs"]

    def _submit(self, d):
        parsed = self._opts(d)
        if not parsed:
            return self._json({"error": "bad_options"}, 400)
        opts, jobs = parsed
        added = 0
        for u in d.get("urls", []):
            if not core.is_url(u):
                continue
            if d.get("playlist"):
                it = STATE.new_item(u, "playlist")
                STATE.get_executor(jobs).submit(run_playlist, it, u, opts, jobs)
            else:
                it = STATE.new_item(u, "url")
                STATE.get_executor(jobs).submit(run_item, it, u, dict(opts))
            added += 1
        self._json({"added": added} if added else {"error": "nothing"}, 200 if added else 400)

    def _upload(self, q):
        """رفع ملف واحد كجسم خام (بدون multipart): خفيف ويشتغل على كل إصدارات بايثون."""
        size = int(self.headers.get("Content-Length") or 0)
        name = (q.get("name") or ["song"])[0]
        if size <= 0 or size > MAX_UPLOAD:
            return self._json({"error": "bad_size"}, 400)
        parsed = self._opts({k: v[0] for k, v in q.items()})
        if not parsed:
            return self._json({"error": "bad_options"}, 400)
        opts, jobs = parsed
        stem, suffix = Path(name).stem, Path(name).suffix
        dest = core.upload_dir() / f"{uuid.uuid4().hex[:8]}_{core.safe_stem(stem)}{suffix}"
        left = size
        with open(dest, "wb") as f:
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left))
                if not chunk:
                    break
                f.write(chunk)
                left -= len(chunk)
        if left:
            dest.unlink()
            return self._json({"error": "incomplete"}, 400)
        it = STATE.new_item(name, "file")
        o = dict(opts, name=stem, keep_original=True, cleanup_source=True)
        STATE.get_executor(jobs).submit(run_item, it, str(dest), o)
        self._json({"added": 1})

    # ---- ملفات (مع دعم Range عشان المشغّل يقدر يقفز داخل الأغنية) ----
    def _serve_file(self, root, name, cache=True):
        root = Path(root).resolve()
        p = (root / name).resolve()
        if root not in p.parents or not p.is_file():
            return self.send_error(404)
        size = p.stat().st_size
        start, end, status = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            end = min(end, size - 1)
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        self.send_header("Content-Type", mimetypes.guess_type(p.name)[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        try:
            with open(p, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass


# ---------- تشغيل / إيقاف ----------

def make_server(mode="browser"):
    """يربط أول منفذ متاح من 8765 وما بعده."""
    STATE.mode = mode
    last_err = None
    for port in range(BASE_PORT, BASE_PORT + 20):
        STATE.port = port
        try:
            httpd = ThreadingHTTPServer((HOST, port), Handler)
            httpd.daemon_threads = True
            STATE.httpd = httpd
            return httpd
        except OSError as e:
            last_err = e
    raise last_err


def stop_server():
    time.sleep(0.2)
    if STATE.httpd:
        STATE.httpd.shutdown()


def restart_app():
    """يشغّل نسخة جديدة من البرنامج ثم يقفل الحالية (بعد التحديث)."""
    time.sleep(0.5)
    args = [sys.executable, str(core.ROOT / "run.py"), *[a for a in sys.argv[1:] if a != "--no-open"]]
    subprocess.Popen(args, cwd=str(core.ROOT), close_fds=True)
    stop_server()


def idle_watchdog():
    """وضع المتصفح فقط: يقفل البرنامج لو الصفحة انقفلت وما فيه مهام شغّالة."""
    while True:
        time.sleep(30)
        if STATE.mode == "browser" and not STATE.busy() and time.time() - STATE.last_seen > IDLE_EXIT_SECONDS:
            stop_server()
            return
