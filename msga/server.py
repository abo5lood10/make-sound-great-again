"""خادم محلي خفيف (مكتبة بايثون القياسية فقط) يقدّم الواجهة والـ API. يستمع على 127.0.0.1 فقط."""
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import core, picker, spotify, updater
from .version import APP_NAME, VERSION

HOST = "127.0.0.1"
BASE_PORT = int(os.environ.get("MSGA_PORT", "8765"))
MAX_UPLOAD = 2 * 1024 * 1024 * 1024  # 2GB
IDLE_EXIT_SECONDS = 600  # وضع المتصفح: لو ما فيه صفحة مفتوحة ولا مهام، يقفل نفسه (خفيف على الجهاز)
HISTORY_MAX = 50
FINAL = ("done", "error", "cancelled")

mimetypes.add_type("font/ttf", ".ttf")
for _ext, _mime in ((".m4a", "audio/mp4"), (".flac", "audio/flac"), (".opus", "audio/ogg"), (".aac", "audio/aac"),
                    (".mp3", "audio/mpeg"), (".wav", "audio/wav"), (".ogg", "audio/ogg"), (".weba", "audio/webm")):
    mimetypes.add_type(_mime, _ext)
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")


def history_path():
    return core.config_dir() / "history.json"


def spectra_dir():
    d = core.config_dir() / "spectra"
    d.mkdir(parents=True, exist_ok=True)
    return d


class State:
    """حالة التطبيق في الذاكرة: قائمة المهام + منفّذ المعالجة. الحقول اللي تبدأ بـ _ خاصة ما تنرسل للواجهة."""

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
        self.finished_batch = 0
        self.spec_lock = threading.Lock()
        self.queue = []          # ترتيب المشغّل (قائمة معرّفات)
        self.tracks = {}         # id -> track dict
        self.tc_locks = {}       # قفل لكل ملف أثناء التحويل المؤقت

    def get_executor(self, jobs):
        if self.executor is None or jobs != self.executor_jobs:
            if self.executor:
                self.executor.shutdown(wait=False)  # اللي بالطابور يكمل، والجديد يروح للتنفيذ الجديد
            self.executor = ThreadPoolExecutor(jobs)
            self.executor_jobs = jobs
        return self.executor

    def new_item(self, label, kind, source=None, opts=None, req=None, src_url=None):
        it = {"id": uuid.uuid4().hex[:10], "label": label, "kind": kind, "status": "waiting",
              "stage_key": None, "pct": 0, "error": None, "result": None, "cached": False,
              "_source": source, "_opts": opts, "_req": req, "_src": src_url, "_token": core.CancelToken(),
              "_future": None, "_paths": {}, "_cleanup": None}
        with self.lock:
            self.items.append(it)
        return it

    def busy(self):
        return any(i["status"] in ("waiting", "running") for i in self.items)

    def find(self, item_id):
        with self.lock:
            return next((i for i in self.items if i["id"] == item_id), None)


STATE = State()


def public(it):
    d = {k: v for k, v in it.items() if not k.startswith("_")}
    d["can_rerun"] = bool(it["_paths"].get("o") and Path(it["_paths"]["o"]).exists())
    d["can_tags"] = bool(it["_paths"].get("e") and Path(it["_paths"]["e"]).exists())
    d["can_retry"] = bool(it["status"] in ("error", "cancelled") and it["_source"]
                          and (it["kind"] != "file" or Path(it["_source"]).is_file()))
    return d


def file_url(path):
    return "/files/" + quote(Path(path).name)


def original_url(it, path):
    """النسخة الأصلية: لو داخل مجلد الحفظ نقدّمها من /files، وإلا (ملف المستخدم الأصلي) من /orig/<id>."""
    if not path:
        return None
    try:
        inside = Path(path).resolve().parent == Path(core.load_config()["out"]).resolve()
    except OSError:
        inside = False
    return file_url(path) if inside else f"/orig/{it['id']}"


def error_dict(e):
    if isinstance(e, core.EnhanceError):
        return {"key": e.key, "params": e.params}
    return {"key": None, "text": str(e)}


def request_key(opts):
    return {"preset": opts.get("preset"), "format": opts.get("format"),
            "bass": int(opts.get("bass", 0)), "treble": int(opts.get("treble", 0)), "lufs": opts.get("lufs", -14)}


# ---------- السجل (يبقى بعد إغلاق البرنامج) ----------

def save_history():
    with STATE.lock:
        done = [i for i in STATE.items if i["status"] == "done" and i["result"]][-HISTORY_MAX:]
        data = [{"id": i["id"], "label": i["label"], "kind": i["kind"], "src": i["_src"], "req": i["_req"],
                 "result": i["result"]} for i in done]
    try:
        history_path().write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def load_history():
    try:
        data = json.loads(history_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    out = Path(core.load_config()["out"])
    items = []
    for e in data:
        r = e.get("result") or {}
        name = r.get("output_name")
        if not name or not (out / name).is_file():
            continue  # الملف انحذف
        it = {"id": e["id"], "label": e.get("label", name), "kind": e.get("kind", "file"), "status": "done",
              "stage_key": "st_done", "pct": 100, "error": None, "result": r, "cached": False,
              "_source": None, "_opts": None, "_req": e.get("req"), "_src": e.get("src"),
              "_token": core.CancelToken(), "_future": None, "_cleanup": None,
              "_paths": {"e": str(out / name)}}
        if r.get("original_name") and (out / r["original_name"]).is_file():
            it["_paths"]["o"] = str(out / r["original_name"])
        elif r.get("original_path") and Path(r["original_path"]).is_file():
            it["_paths"]["o"] = r["original_path"]
            r["original_url"] = f"/orig/{it['id']}"
        items.append(it)
    with STATE.lock:
        STATE.items[:0] = items


def prune_uploads(max_age=2 * 86400):
    """يحذف ملفات مرفوعة قديمة (بقايا مهام فاشلة)."""
    cutoff = time.time() - max_age
    for f in core.upload_dir().iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


# ---------- إشعار سطح المكتب (محاولة بأفضل جهد، بدون مكتبات) ----------

def notify(title, body):
    def esc(s):
        return re.sub(r"[\"'`$\\]", "", s)
    try:
        if core.IS_MAC:
            subprocess.Popen(["osascript", "-e", f'display notification "{esc(body)}" with title "{esc(title)}"'])
        elif core.IS_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; "
                  "$n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; "
                  f"$n.Visible = $true; $n.ShowBalloonTip(6000, '{esc(title)}', '{esc(body)}', 'None'); "
                  "Start-Sleep -Seconds 7; $n.Dispose()")
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                             creationflags=0x08000000)
        elif shutil.which("notify-send"):
            subprocess.Popen(["notify-send", "-i", str(core.ROOT / "assets" / "icon.png"), title, body])
    except Exception:
        pass


def maybe_notify():
    if STATE.busy() or not STATE.finished_batch:
        return
    n, STATE.finished_batch = STATE.finished_batch, 0
    cfg = core.load_config()
    if cfg["notify"]:
        notify(APP_NAME, f"{n} song(s) enhanced" if cfg["lang"] == "en" else f"تمت معالجة {n} أغنية")


# ---------- تنفيذ المهام ----------

def run_item(it):
    token = it["_token"]

    def cb(stage, frac):
        it.update(stage_key=stage, pct=round(frac * 100))

    if token.is_set():
        it.update(status="cancelled", error=None)
        return
    it.update(status="running", error=None, pct=0, stage_key=None)
    opts = dict(it["_opts"], token=token)
    try:
        res = core.process_item(it["_source"], opts, cb)
        r = res["report"]
        r.update(title=res["title"], output_url=file_url(res["output"]),
                 original_url=original_url(it, res["original"]),
                 output_name=Path(res["output"]).name,
                 original_name=Path(res["original"]).name if res["original"] else None,
                 original_path=res["original"])
        it["_paths"] = {"e": res["output"], "o": res["original"]}
        it.update(status="done", stage_key="st_done", pct=100, result=r)
        STATE.finished_batch += 1
        if it["_cleanup"]:
            try:
                Path(it["_cleanup"]).unlink()
            except OSError:
                pass
            it["_cleanup"] = None
        save_history()
    except core.EnhanceError as e:
        if e.key == "err_cancelled":
            it.update(status="cancelled", error=None)
        else:
            it.update(status="error", error=error_dict(e))
    except Exception as e:  # خطأ غير متوقع: نعرضه بدل ما تنهار الواجهة
        it.update(status="error", error=error_dict(e))
    finally:
        maybe_notify()


def looks_like_playlist(url):
    """قوائم يوتيوب (playlist?list=) وساوندكلاود (/sets/) نكتشفها تلقائيًا. رابط فيديو داخل قائمة يبقى فيديو."""
    u = str(url).lower()
    return ("youtube.com/playlist" in u or "/sets/" in u or "music.youtube.com/playlist" in u
            or ("list=" in u and "v=" not in u and "youtu" in u))


def run_playlist(it, jobs):
    it.update(status="running", stage_key="reading_playlist")
    src, children = it["_source"], []
    try:
        if spotify.is_spotify(src):
            for t in spotify.fetch(src)["tracks"]:
                name = spotify.display_name(t)
                o = dict(it["_opts"], name=core.safe_stem(name), duration_ms=t["duration_ms"],
                         meta={"title": t["title"], "artist": t["artist"], "album": t["album"]})
                children.append((name, spotify.search_source(t), o))
        else:
            for u in core.expand_playlist(src):
                children.append((u, u, dict(it["_opts"])))
    except core.EnhanceError as e:
        it.update(status="error", error=error_dict(e))
        return
    with STATE.lock:
        if it in STATE.items:
            STATE.items.remove(it)
    for label, source, o in children:
        submit_item(STATE.new_item(label, "url", source=source, opts=o, req=request_key(o), src_url=source), jobs)


def submit_item(it, jobs):
    it["_future"] = STATE.get_executor(jobs).submit(run_item, it)


def add_local(path, opts, jobs, label=None, kind="path"):
    """ملف على جهاز المستخدم: يُعالَج من مكانه بدون نسخ (النسخة الأصلية تبقى ملفه)."""
    path = Path(path)
    o = dict(opts, name=path.stem, keep_original=False, original_override=str(path))
    it = STATE.new_item(label or path.name, kind, source=str(path), opts=o, req=request_key(opts), src_url=str(path))
    submit_item(it, jobs)
    return it


def hard_exit():
    """يقفل العملية بالكامل (حتى النافذة)، لأن serve_forever ما يقفل نافذة البرنامج."""
    time.sleep(0.8)
    os._exit(0)


# ---------- مراقبة مجلد: أي أغنية جديدة تنزل فيه تُحسَّن تلقائيًا ----------
WATCH_INTERVAL = 15
_watch_sizes = {}


def watch_seen_path():
    return core.config_dir() / "watch_seen.json"


def _load_seen():
    try:
        return set(json.loads(watch_seen_path().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _save_seen(seen):
    try:
        watch_seen_path().write_text(json.dumps(sorted(seen)[-5000:], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def watch_scan():
    """دورة وحدة: يرجع عدد الملفات اللي أُضيفت. أول مرة على مجلد: يسجّل اللي فيه فقط (ما يعالج القديم)."""
    cfg = core.load_config()
    folder = Path(cfg["watch"]).expanduser() if cfg["watch"] else None
    if not cfg["watch_on"] or not folder or not folder.is_dir():
        return 0
    out = Path(cfg["out"]).resolve()
    seen = _load_seen()
    marker = f"__baseline__|{folder.resolve()}"
    baseline = marker not in seen
    added = 0
    for f in core.collect_media([str(folder)]):
        if out in f.parents or f.stem.endswith(("_enhanced", "_original")):
            continue  # ما نعالج مخرجاتنا
        try:
            st = f.stat()
        except OSError:
            continue
        key = f"{f}|{int(st.st_mtime)}|{st.st_size}"
        if key in seen:
            continue
        if baseline:
            seen.add(key)
            continue
        # نتأكد إن الملف خلص نسخ: حجمه ثابت بين دورتين وعمره أكثر من 5 ثواني
        if _watch_sizes.get(str(f)) != st.st_size or time.time() - st.st_mtime < 5:
            _watch_sizes[str(f)] = st.st_size
            continue
        seen.add(key)
        parsed = Handler._opts_static(cfg)
        add_local(f, parsed[0], parsed[1], label=f.name, kind="watch")
        added += 1
    if baseline:
        seen.add(marker)
    _save_seen(seen)
    return added


def watcher_loop():
    while True:
        time.sleep(WATCH_INTERVAL)
        try:
            watch_scan()
        except Exception:
            pass


def open_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    if core.IS_WIN:
        os.startfile(str(path))  # noqa: S606
    elif core.IS_MAC:
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def public_track(t):
    return {"id": t["id"], "name": t["name"], "ext": t["ext"], "title": t.get("title"), "artist": t.get("artist"),
            "album": t.get("album"), "duration": t.get("duration"), "has_cover": t.get("has_cover")}


def player_state():
    return {"tracks": [public_track(STATE.tracks[i]) for i in STATE.queue if i in STATE.tracks]}


def player_add(paths, append=False, only_new=True):
    """يسجّل ملفات (أو مجلدات) في قائمة المشغّل. يرجع معرّف آخر ملف أُضيف."""
    import hashlib
    if not append:
        STATE.queue.clear()
        STATE.tracks.clear()
    last = None
    for f in core.collect_media(paths):
        tid = hashlib.sha1(str(f).encode("utf-8")).hexdigest()[:10]
        if tid in STATE.tracks and only_new and append:
            last = tid
            continue
        STATE.tracks.setdefault(tid, {"id": tid, "path": str(f), "name": f.stem, "ext": f.suffix.lower().lstrip(".")})
        if tid not in STATE.queue or not only_new:
            if tid in STATE.queue and not only_new:
                last = tid
                continue
            STATE.queue.append(tid)
        last = tid
    return last


class QuietServer(ThreadingHTTPServer):
    """النافذة أحيانًا تقطع الاتصال في نص الرد (طبيعي): ما نطبع أخطاء الاتصال المقطوع."""

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (ConnectionError, BrokenPipeError, TimeoutError)):
            return
        super().handle_error(request, client_address)


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
        url = urlparse(self.path)
        path = url.path
        if path == "/":
            self._serve_file(core.WEB_DIR, "index.html", cache=False)
        elif path.startswith("/static/"):
            name = unquote(path[8:])
            # js/css لازم تتحدّث مع كل إصدار (كاش طويل يخلي الواجهة القديمة تبقى بعد التحديث)؛ الخطوط والصور كاش طويل
            self._serve_file(core.WEB_DIR, name, cache=name.endswith((".ttf", ".svg", ".png")))
        elif path.startswith("/files/"):
            self._serve_file(Path(core.load_config()["out"]), unquote(path[7:]), cache=False)
        elif path.startswith("/orig/"):
            it = STATE.find(unquote(path[6:]))
            p = Path(it["_paths"].get("o") or "") if it else None
            if p and p.is_file():
                self._serve_file(p.parent, p.name, cache=False)
            else:
                self.send_error(404)
        elif path.startswith("/play/"):
            self._play(unquote(path[6:]), parse_qs(url.query))
        elif path == "/api/player/tracks":
            self._json(player_state())
        elif path == "/api/player/meta":
            self._player_meta(parse_qs(url.query))
        elif path == "/api/player/cover":
            self._player_cover(parse_qs(url.query))
        elif path == "/api/tags":
            self._get_tags(parse_qs(url.query))
        elif path == "/api/update/progress":
            self._json(updater.PROGRESS)
        elif path == "/api/ping":
            self._json({"ok": True, "app": APP_NAME, "mode": STATE.mode, "version": VERSION})
        elif path == "/api/messages":
            self._json(core.MESSAGES)
        elif path == "/api/state":
            self._json(self._state())
        elif path == "/api/spectrogram":
            self._spectrogram(parse_qs(url.query))
        else:
            self.send_error(404)

    def _state(self):
        if STATE.thmanyah is None:
            STATE.thmanyah = core.find_thmanyah()
        with STATE.lock:
            items = [public(i) for i in STATE.items]
        return {"app": APP_NAME, "version": VERSION, "mode": STATE.mode, "config": core.load_config(),
                "items": items, "presets": list(core.PRESETS), "formats": list(core.CODECS),
                "thmanyah": STATE.thmanyah, "missing": core.missing_tools(need_download=True),
                "repo_url": updater.repo_url(), "releases_url": updater.releases_url(),
                "frozen": updater.FROZEN, "platform": sys.platform, "pick": picker.available(),
                "ai_models": all((core.MODELS_DIR / n).is_file() for n in ("mp.rnnn", "bd.rnnn"))}

    def _spectrogram(self, q):
        it = STATE.find((q.get("id") or [""])[0])
        which = (q.get("which") or ["e"])[0]
        path = it["_paths"].get(which) if it else None
        if not path or not Path(path).is_file():
            return self._json({"error": "not_found"}, 404)
        p = Path(path)
        key = hashlib.sha1(f"{p}|{p.stat().st_mtime_ns}".encode()).hexdigest()[:16]
        out = spectra_dir() / f"{key}.png"
        if not out.exists():
            core.set_light(core.load_config()["light"])
            with STATE.spec_lock:  # واحد واحد عشان الجهاز يبقى خفيف
                try:
                    if not out.exists():
                        core.spectrogram(p, out)
                except core.EnhanceError as e:
                    return self._json({"error": e.key}, 500)
        self._serve_file(spectra_dir(), out.name)

    # ---- POST ----
    def do_POST(self):
        if not self._guard():
            return
        url = urlparse(self.path)
        path = url.path
        if path == "/api/upload":
            return self._upload(parse_qs(url.query))
        if path == "/api/cover":
            return self._cover(parse_qs(url.query))
        d = self._read_json()
        routes = {
            "/api/submit": self._submit, "/api/cancel": self._cancel, "/api/retry": self._retry,
            "/api/reprocess": self._reprocess, "/api/config": self._config, "/api/clear": self._clear,
            "/api/clean": self._clean, "/api/open": self._open, "/api/open_repo": self._open_repo,
            "/api/update/check": self._upd_check, "/api/update/apply": self._upd_apply,
            "/api/update/ytdlp": self._upd_ytdlp, "/api/ytdlp/version": self._ytdlp_version,
            "/api/restart": self._restart, "/api/quit": self._quit,
            "/api/pick": self._pick, "/api/submit_paths": self._submit_paths, "/api/tags": self._set_tags,
            "/api/player/open": self._player_open, "/api/player/paths": self._player_paths,
            "/api/player/add_item": self._player_add_item, "/api/player/clear": self._player_clear,
        }
        fn = routes.get(path)
        if fn:
            fn(d)
        else:
            self.send_error(404)

    @staticmethod
    def _opts_static(cfg):
        return {"preset": cfg["preset"], "format": cfg["format"], "out_dir": cfg["out"], "light": cfg["light"],
                "bass": cfg["bass"], "treble": cfg["treble"], "lufs": cfg["lufs"]}, cfg["jobs"]

    def _opts(self, d):
        cfg = core.load_config()
        preset = d.get("preset", cfg["preset"])
        fmt = d.get("format", cfg["format"])
        if preset not in (*core.PRESETS, "auto") or fmt not in core.CODECS:
            return None
        try:
            bass = max(-6, min(6, int(d.get("bass", cfg["bass"]))))
            treble = max(-6, min(6, int(d.get("treble", cfg["treble"]))))
        except (TypeError, ValueError):
            return None
        try:
            lufs = int(d.get("lufs", cfg["lufs"]))
        except (TypeError, ValueError):
            return None
        if lufs not in core.LUFS_CHOICES:
            return None
        return {"preset": preset, "format": fmt, "out_dir": cfg["out"], "light": cfg["light"],
                "bass": bass, "treble": treble, "lufs": lufs, "keep_original": cfg["keep_original"]}, cfg["jobs"]

    def _submit(self, d):
        parsed = self._opts(d)
        if not parsed:
            return self._json({"error": "bad_options"}, 400)
        opts, jobs = parsed
        added = 0
        for u in d.get("urls", []):
            if not core.is_url(u) and not spotify.is_spotify(u):
                continue
            req = request_key(opts)
            if d.get("playlist") or spotify.is_spotify(u) or looks_like_playlist(u):
                it = STATE.new_item(u, "playlist", source=u, opts=dict(opts), req=req, src_url=u)
                it["_future"] = STATE.get_executor(jobs).submit(run_playlist, it, jobs)
            else:
                cached = self._cached(u, req)
                if cached:  # نفس الرابط ونفس الإعدادات ومعالَج من قبل: نعرض النتيجة بدل ما نعيد الشغل
                    it = STATE.new_item(cached["label"], "url", opts=dict(opts), req=req, src_url=u)
                    it.update(status="done", stage_key="st_done", pct=100, result=cached["result"], cached=True)
                    it["_paths"] = dict(cached["_paths"])
                else:
                    it = STATE.new_item(u, "url", source=u, opts=dict(opts), req=req, src_url=u)
                    submit_item(it, jobs)
            added += 1
        self._json({"added": added} if added else {"error": "nothing"}, 200 if added else 400)

    def _cached(self, url, req):
        with STATE.lock:
            for i in reversed(STATE.items):
                if (i["status"] == "done" and i["_src"] == url and i["_req"] == req
                        and i["_paths"].get("e") and Path(i["_paths"]["e"]).is_file()):
                    return i
        return None

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
        o = dict(opts, name=stem)
        it = STATE.new_item(name, "file", source=str(dest), opts=o, req=request_key(opts))
        it["_cleanup"] = str(dest)  # نحذفه لما ينجح (ونبقيه لو فشل عشان "إعادة المحاولة")
        submit_item(it, jobs)
        self._json({"added": 1})

    def _cancel(self, d):
        it = STATE.find(d.get("id", ""))
        if not it or it["status"] not in ("waiting", "running"):
            return self._json({"ok": False})
        it["_token"].cancel()
        fut = it.get("_future")
        if (fut is not None and fut.cancel()) or it["status"] == "waiting":  # ما بدأ أصلًا
            it.update(status="cancelled", error=None)
        self._json({"ok": True})

    def _retry(self, d):
        it = STATE.find(d.get("id", ""))
        if not it or it["status"] not in ("error", "cancelled") or not it["_source"]:
            return self._json({"ok": False})
        if it["kind"] == "file" and not Path(it["_source"]).is_file():
            return self._json({"ok": False})
        jobs = core.load_config()["jobs"]
        it.update(status="waiting", error=None, pct=0, stage_key=None, _token=core.CancelToken())
        submit_item(it, jobs)
        self._json({"ok": True})

    def _reprocess(self, d):
        """يعيد معالجة أغنية خلصت بنمط/إعدادات ثانية من نسختها الأصلية (بدون تنزيل من جديد)."""
        it = STATE.find(d.get("id", ""))
        orig = it["_paths"].get("o") if it else None
        parsed = self._opts(d)
        if not it or not orig or not Path(orig).is_file() or not parsed:
            return self._json({"ok": False}, 400)
        opts, jobs = parsed
        o = dict(opts, name=it["result"]["title"], keep_original=False, original_override=orig)
        new = STATE.new_item(it["label"], it["kind"], source=orig, opts=o, req=request_key(opts), src_url=it["_src"])
        submit_item(new, jobs)
        self._json({"ok": True})

    def _config(self, d):
        core.save_config({**core.load_config(), **d})
        self._json({"config": core.load_config()})

    def _clear(self, _d):
        with STATE.lock:
            gone = [i for i in STATE.items if i["status"] in FINAL]
            STATE.items[:] = [i for i in STATE.items if i["status"] not in FINAL]
        for i in gone:  # ملفات مرفوعة بقيت لإعادة المحاولة
            if i.get("_cleanup"):
                try:
                    Path(i["_cleanup"]).unlink()
                except OSError:
                    pass
        save_history()
        self._json({"ok": True})

    def _clean(self, d):
        try:
            days = max(0, int(d.get("days", 30)))
        except (TypeError, ValueError):
            days = 30
        self._json({"deleted": core.clean_old(core.load_config()["out"], days)})

    def _open(self, _d):
        open_folder(core.load_config()["out"])
        self._json({"ok": True})

    def _open_repo(self, d):
        url = updater.releases_url() if d.get("releases") else updater.repo_url()
        if url:
            webbrowser.open(url)
        self._json({"ok": bool(url)})

    def _upd_check(self, d):
        self._json(updater.check(use_cache=bool(d.get("cached"))))

    def _upd_apply(self, _d):
        res = updater.apply()
        self._json(res)
        if res.get("ok") and res.get("exit"):  # النسخة الجاهزة: السكربت ينتظر خروجنا ثم يستبدل ويعيد التشغيل
            threading.Thread(target=hard_exit, daemon=True).start()

    def _upd_ytdlp(self, _d):
        self._json(updater.update_ytdlp())

    def _ytdlp_version(self, _d):
        self._json({"version": updater.ytdlp_version()})

    def _restart(self, _d):
        self._json({"ok": True})
        threading.Thread(target=restart_app, daemon=True).start()

    # ---- المشغّل ----
    def _player_open(self, d):
        kind = "folder" if d.get("kind") == "folder" else "files"
        try:
            paths = picker.pick(kind)
        except Exception:
            paths = None
        if paths is None:
            return self._json({"error": "no_dialog"}, 501)
        if paths:
            player_add(paths, append=bool(d.get("append")))
        self._json(player_state())

    def _player_paths(self, d):
        player_add([p for p in d.get("paths", []) if isinstance(p, str)], append=bool(d.get("append")))
        self._json(player_state())

    def _player_add_item(self, d):
        it = STATE.find(d.get("id", ""))
        p = it["_paths"].get("e") if it else None
        if not p or not Path(p).is_file():
            return self._json({"error": "not_found"}, 404)
        before = len(STATE.queue)
        tid = player_add([p], append=True, only_new=False)
        state = player_state()
        state["index"] = STATE.queue.index(tid) if tid in STATE.queue else max(0, before)
        self._json(state)

    def _player_clear(self, _d):
        STATE.queue.clear()
        STATE.tracks.clear()
        self._json(player_state())

    def _player_meta(self, q):
        t = STATE.tracks.get((q.get("id") or [""])[0])
        if not t:
            return self._json({"error": "not_found"}, 404)
        if not t.get("meta_loaded"):
            try:
                core.set_light(core.load_config()["light"])
                tags = core.read_tags(t["path"])
                t.update(title=tags["title"] or None, artist=tags["artist"] or None, album=tags["album"] or None,
                         has_cover=tags["has_cover"], duration=core.media_duration(t["path"]))
            except core.EnhanceError:
                pass
            t["meta_loaded"] = True
        self._json(public_track(t))

    def _player_cover(self, q):
        t = STATE.tracks.get((q.get("id") or [""])[0])
        img = None
        if t and Path(t["path"]).is_file():
            core.set_light(core.load_config()["light"])
            img = core.extract_cover_image(t["path"])
        if not img:
            return self.send_error(404)
        self._serve_file(core.play_cache_dir(), img.name)

    def _play(self, tid, q):
        """يقدّم الملف مباشرة، أو (للصيغ اللي المتصفح ما يشغّلها) نسخة MP3 مؤقتة تقبل التقديم والتأخير."""
        t = STATE.tracks.get(tid)
        if not t or not Path(t["path"]).is_file():
            return self.send_error(404)
        p = Path(t["path"])
        if (q.get("mode") or [""])[0] == "transcode":
            key = str(p)
            lock = STATE.tc_locks.setdefault(key, threading.Lock())
            with lock:  # نفس الملف ما ينحوّل مرتين
                try:
                    core.set_light(core.load_config()["light"])
                    out = core.transcode_for_play(p)
                except core.EnhanceError:
                    return self.send_error(500)
            return self._serve_file(out.parent, out.name, cache=False)
        self._serve_file(p.parent, p.name, cache=False)

    # ---- اختيار ملفات / مجلدات ومعالجتها من مكانها (بدون نسخ) ----
    def _pick(self, d):
        kind = "folder" if d.get("kind") == "folder" else "files"
        try:
            paths = picker.pick(kind)
        except Exception:
            paths = None
        if paths is None:
            return self._json({"error": "no_dialog"}, 501)
        self._json({"paths": paths})

    def _submit_paths(self, d):
        parsed = self._opts(d)
        if not parsed:
            return self._json({"error": "bad_options"}, 400)
        opts, jobs = parsed
        files = core.collect_media([p for p in d.get("paths", []) if isinstance(p, str)])
        for f in files:
            add_local(f, opts, jobs)
        self._json({"added": len(files)} if files else {"error": "nothing"}, 200 if files else 400)

    # ---- بيانات الأغنية (التاغات) والغلاف ----
    def _tag_target(self, item_id):
        it = STATE.find(item_id or "")
        p = it["_paths"].get("e") if it else None
        return Path(p) if p and Path(p).is_file() else None

    def _get_tags(self, q):
        p = self._tag_target((q.get("id") or [""])[0])
        if not p:
            return self._json({"error": "not_found"}, 404)
        try:
            self._json({**core.read_tags(p), "cover_ok": p.suffix.lower().lstrip(".") in core.COVER_FORMATS})
        except core.EnhanceError as e:
            self._json({"error": e.key}, 500)

    def _set_tags(self, d):
        p = self._tag_target(d.get("id"))
        if not p:
            return self._json({"error": "not_found"}, 404)
        tags = {k: str(d[k])[:300] for k in core.TAG_KEYS if k in d}
        try:
            core.set_light(core.load_config()["light"])
            core.write_tags(p, tags)
            self._json({"ok": True})
        except core.EnhanceError as e:
            self._json({"error": e.key}, 500)

    def _cover(self, q):
        size = int(self.headers.get("Content-Length") or 0)
        p = self._tag_target((q.get("id") or [""])[0])
        if not p or size <= 0 or size > 10 * 1024 * 1024:
            self.rfile.read(max(0, min(size, 10 * 1024 * 1024)))
            return self._json({"error": "bad_request"}, 400)
        data = self.rfile.read(size)
        ext = ".png" if data[:4] == b"\x89PNG" else ".jpg" if data[:2] == b"\xff\xd8" else None
        if not ext:
            return self._json({"error": "bad_image"}, 400)
        tmp = core.upload_dir() / f"cover_{uuid.uuid4().hex[:8]}{ext}"
        try:
            tmp.write_bytes(data)
            core.set_light(core.load_config()["light"])
            core.write_tags(p, {}, cover=tmp)
            self._json({"ok": True})
        except core.EnhanceError as e:
            self._json({"error": e.key}, 500)
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass

    def _quit(self, _d):
        self._json({"ok": True})
        threading.Thread(target=stop_server, daemon=True).start()

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
    """يربط أول منفذ متاح من 8765 وما بعده، ويجهّز السجل والتحديث التلقائي لمحرك التنزيل."""
    STATE.mode = mode
    core.set_engine_updater(updater.auto_update_engine)
    last_err = None
    for port in range(BASE_PORT, BASE_PORT + 20):
        STATE.port = port
        try:
            httpd = QuietServer((HOST, port), Handler)
            httpd.daemon_threads = True
            STATE.httpd = httpd
            if not STATE.items:
                load_history()
            prune_uploads()
            threading.Thread(target=watcher_loop, daemon=True).start()
            return httpd
        except OSError as e:
            last_err = e
    raise last_err


def stop_server():
    time.sleep(0.2)
    for it in list(STATE.items):  # نوقف أي شغل جاري
        if it["status"] in ("waiting", "running"):
            it["_token"].cancel()
    if STATE.httpd:
        STATE.httpd.shutdown()


def restart_app():
    """يشغّل نسخة جديدة من البرنامج ثم يقفل الحالية (بعد التحديث)."""
    time.sleep(0.5)
    rest = [a for a in sys.argv[1:] if a != "--no-open"]
    if getattr(sys, "frozen", False):
        args = [sys.executable, *rest]
    else:
        args = [sys.executable, str(core.ROOT / "run.py"), *rest]
    subprocess.Popen(args, cwd=str(core.ROOT), close_fds=True)
    for it in list(STATE.items):
        if it["status"] in ("waiting", "running"):
            it["_token"].cancel()
    os._exit(0)


def idle_watchdog():
    """وضع المتصفح فقط: يقفل البرنامج لو الصفحة انقفلت وما فيه مهام شغّالة."""
    while True:
        time.sleep(30)
        if STATE.mode == "browser" and not STATE.busy() and time.time() - STATE.last_seen > IDLE_EXIT_SECONDS:
            stop_server()
            return
