"""محرك Make Sound Great Again: تنزيل، تحليل جودة المصدر، معالجة بمرحلتين، وحفظ مع الغلاف والبيانات.

يشتغل على Windows وmacOS وLinux، ولا يحتاج غير مكتبة بايثون القياسية (مع ffmpeg وyt-dlp).
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
PKG_DIR = Path(__file__).resolve().parent
ROOT = PKG_DIR.parent
WEB_DIR = PKG_DIR / "web"


def _extend_path():
    """تطبيقات الواجهة (Finder / قائمة ابدأ) غالبًا PATH فيها ناقص، فنضيف أماكن التثبيت المعروفة."""
    extra = [str(ROOT / "bin")]  # ffmpeg / ffprobe المضمّنين مع النسخة الجاهزة (لو موجودين)
    if IS_MAC:
        extra += ["/opt/homebrew/bin", "/usr/local/bin"]
    elif not IS_WIN:
        extra += [str(Path.home() / ".local" / "bin"), "/usr/local/bin"]
    scripts = Path(sys.executable).parent / ("Scripts" if IS_WIN else "bin")
    extra.append(str(scripts))
    os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])


_extend_path()


# ---------- مجلدات المستخدم (حسب النظام) ----------

def config_dir():
    override = os.environ.get("MSGA_HOME")
    if override:
        base = Path(override)
    elif IS_WIN:
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "MakeSoundGreatAgain"
    elif IS_MAC:
        base = Path.home() / "Library" / "Application Support" / "MakeSoundGreatAgain"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "make-sound-great-again"
    base.mkdir(parents=True, exist_ok=True)
    return base


def upload_dir():
    d = config_dir() / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


DEFAULT_OUT = str(Path.home() / "Music" / "Make Sound Great Again")
DEFAULT_CONFIG = {"preset": "auto", "format": "flac", "jobs": 1, "out": DEFAULT_OUT,
                  "lang": "ar", "theme": "system", "light": True,
                  "bass": 0, "treble": 0, "notify": True, "auto_check": True,
                  "lufs": -14, "watch": "", "watch_on": False}
LUFS_CHOICES = (0, -9, -11, -14, -16)  # 0 = بدون تطبيع

# ملاحظة: كل النماذج تنتهي بتطبيع مستوى الصوت (مرحلتين) وlimiter عشان ما يصير تشويه.
PRESETS = {
    # خفيف جدًا: للمصادر عالية الجودة، تقريبًا تطبيع مستوى فقط
    "gentle": [
        "highpass=f=20",
        "equalizer=f=100:t=q:w=1:g=0.8",
        "equalizer=f=3500:t=q:w=1:g=0.8",
    ],
    "natural": [
        "highpass=f=25",
        "afftdn=nr=6:nf=-45",
        "equalizer=f=100:t=q:w=1:g=1.5",
        "equalizer=f=3500:t=q:w=1:g=1.5",
        "aexciter=amount=1.5:drive=6:freq=7000",
    ],
    # للمقاطع الضعيفة والمضغوطة (تيكتوك/انستا)
    "clean": [
        "highpass=f=40",
        "afftdn=nr=12:nf=-40",
        "equalizer=f=200:t=q:w=1:g=-1.5",
        "equalizer=f=3000:t=q:w=1:g=2.5",
        "aexciter=amount=2.5:drive=8:freq=6000",
        "acompressor=threshold=-20dB:ratio=2:attack=20:release=250",
    ],
    "bass": [
        "highpass=f=25",
        "afftdn=nr=6:nf=-45",
        "equalizer=f=60:t=q:w=0.9:g=4",
        "equalizer=f=120:t=q:w=1:g=2",
        "equalizer=f=3500:t=q:w=1:g=1",
        "aexciter=amount=1.5:drive=6:freq=7000",
    ],
    "vocal": [
        "highpass=f=60",
        "afftdn=nr=8:nf=-42",
        "equalizer=f=250:t=q:w=1:g=-1.5",
        "equalizer=f=2500:t=q:w=1:g=3",
        "equalizer=f=5000:t=q:w=1:g=1.5",
        "aexciter=amount=2:drive=7:freq=6500",
    ],
    # ذكاء اصطناعي خفيف (RNNoise عبر فلتر arnndn في ffmpeg): ما يُختار تلقائيًا، فقط لو اخترته
    "ai_music": [  # موديل mp: صوت عام مع ضوضاء عامة. mix يخلّط مع الأصل عشان ما يضر الآلات
        "highpass=f=20",
        "arnndn=m=mp.rnnn:mix=0.85",
    ],
    "ai_voice": [  # موديل bd: كلام مع ضوضاء تسجيل (مقاطع تيكتوك / انستا اللي فيها شخص يتكلم)
        "highpass=f=70",
        "arnndn=m=bd.rnnn",
        "equalizer=f=3000:t=q:w=1:g=2",
    ],
}
AUTO_MAP = {"low": "clean", "mid": "natural", "high": "gentle"}
MODELS_DIR = PKG_DIR / "models"

CODECS = {
    "flac": ["-c:a", "flac", "-sample_fmt", "s32", "-ar", "48000"],
    "mp3": ["-c:a", "libmp3lame", "-b:a", "320k", "-ar", "48000", "-id3v2_version", "3"],
    "m4a": ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"],
    "opus": ["-c:a", "libopus", "-b:a", "192k", "-ar", "48000"],
    "wav": ["-c:a", "pcm_s24le", "-ar", "48000"],
}
COVER_FORMATS = ("flac", "mp3", "m4a")  # الصيغ اللي تقبل صورة الغلاف داخل الملف

LOUDNORM = "loudnorm=I=-14:TP=-1.0:LRA=11"  # للقياس/التحليل فقط


def loudnorm_filter(target):
    return f"loudnorm=I={target}:TP=-1.0:LRA=11"
LOSSLESS = ("flac", "alac", "wav", "ape", "wavpack", "tta")

MESSAGES = {
    # مراحل المعالجة
    "st_download": ("تنزيل", "Downloading"),
    "st_analyze": ("تحليل جودة المصدر", "Analyzing source"),
    "st_measure": ("قياس مستوى الصوت", "Measuring loudness"),
    "st_process": ("معالجة وحفظ", "Processing & saving"),
    "st_engine": ("تحديث محرك التنزيل", "Updating the download engine"),
    "st_done": ("تم", "Done"),
    # الأخطاء
    "err_tools": ("ناقص برنامج: {tools}", "Missing program(s): {tools}"),
    "err_private": ("الفيديو خاص، ما أقدر أنزله.", "This video is private and can't be downloaded."),
    "err_unavail": ("الفيديو محذوف أو غير متاح.", "The video was removed or is unavailable."),
    "err_signin": ("الموقع يطلب تسجيل دخول أو تحقق، جرّب رابط ثاني.", "The site requires sign-in or verification. Try another link."),
    "err_unsupported": ("الرابط غير مدعوم.", "This link isn't supported."),
    "err_404": ("الرابط غير موجود (404)، تأكد منه.", "Link not found (404). Please check it."),
    "err_geo": ("المقطع محجوب في منطقتك.", "This clip is blocked in your region."),
    "err_blocked": ("الموقع رفض الطلب مؤقتًا، جرّب بعد شوي.", "The site refused the request for now. Try again shortly."),
    "err_network": ("ما قدرت أوصل للموقع، تأكد من الإنترنت.", "Couldn't reach the site. Check your internet connection."),
    "err_format": ("ما لقيت صوت قابل للتنزيل في هذا الرابط.", "No downloadable audio was found at this link."),
    "err_dl": ("فشل التنزيل{detail}", "Download failed{detail}"),
    "err_nofile": ("ما لقيت الملف بعد التنزيل.", "The file wasn't found after download."),
    "err_ffmpeg": ("فشلت المعالجة: {tail}", "Processing failed: {tail}"),
    "err_unreadable": ("ما قدرت أقرأ الملف، تأكد إنه ملف صوت صحيح.", "Couldn't read the file. Make sure it's a valid audio file."),
    "err_noaudio": ("الملف ما فيه صوت.", "The file has no audio."),
    "err_model": ("ملف موديل الذكاء الاصطناعي ناقص: {name}", "The AI model file is missing: {name}"),
    "err_tags": ("تعذّر حفظ البيانات (التاغات) في هذا الملف", "Couldn't save the tags into this file"),
    "err_cancelled": ("تم الإلغاء", "Cancelled"),
    "err_notfound": ("ما لقيت الملف: {source}", "File not found: {source}"),
    # أسباب تقدير الجودة
    "why_lossless": ("ملف بدون ضغط (Lossless)", "Uncompressed (lossless) file"),
    "why_low_br": ("معدل البت منخفض (\u2066{kbps} kbps\u2069)", "Low bitrate (\u2066{kbps} kbps\u2069)"),
    "why_hf_cut": ("الترددات العالية (فوق 16kHz) شبه مقطوعة، علامة ضغط قوي",
                   "Frequencies above 16kHz are nearly cut off, a sign of heavy compression"),
    "why_high_br": ("معدل بت عالي (\u2066{kbps} kbps\u2069)", "High bitrate (\u2066{kbps} kbps\u2069)"),
    "why_mid_br": ("جودة متوسطة (\u2066{kbps} kbps\u2069)", "Medium quality (\u2066{kbps} kbps\u2069)"),
    "why_mid": ("جودة متوسطة", "Medium quality"),
}


def msg(key, lang="ar", **kw):
    ar, en = MESSAGES[key]
    return (en if lang == "en" else ar).format(**kw)


class EnhanceError(Exception):
    """خطأ برسالة جاهزة للمستخدم. str(e) بالعربي، و e.text(lang) بأي لغة."""

    def __init__(self, key, **params):
        self.key, self.params = key, params
        super().__init__(msg(key, "ar", **params))

    def text(self, lang="ar"):
        return msg(self.key, lang, **self.params)


# ---------- الإعدادات ----------

def config_path():
    return config_dir() / "config.json"


def sanitize_config(cfg):
    out = dict(DEFAULT_CONFIG)
    if cfg.get("preset") in (*PRESETS, "auto"):
        out["preset"] = cfg["preset"]
    if cfg.get("format") in CODECS:
        out["format"] = cfg["format"]
    try:
        out["jobs"] = max(1, min(8, int(cfg.get("jobs", out["jobs"]))))
    except (TypeError, ValueError):
        pass
    if cfg.get("out"):
        out["out"] = str(cfg["out"])
    if cfg.get("lang") in ("ar", "en"):
        out["lang"] = cfg["lang"]
    if cfg.get("theme") in ("system", "light", "dark"):
        out["theme"] = cfg["theme"]
    for key in ("light", "notify", "auto_check"):
        if isinstance(cfg.get(key), bool):
            out[key] = cfg[key]
    if cfg.get("lufs") in LUFS_CHOICES:
        out["lufs"] = cfg["lufs"]
    if isinstance(cfg.get("watch"), str):
        out["watch"] = cfg["watch"].strip()
    if isinstance(cfg.get("watch_on"), bool):
        out["watch_on"] = cfg["watch_on"]
    for key in ("bass", "treble"):
        try:
            out[key] = max(-6, min(6, int(cfg.get(key, 0))))
        except (TypeError, ValueError):
            pass
    return out


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(json.loads(config_path().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return sanitize_config(cfg)


def save_config(cfg):
    config_path().write_text(json.dumps(sanitize_config(cfg), ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- تشغيل البرامج الخارجية (يشتغل على كل الأنظمة، وبأولوية منخفضة عشان الجهاز يبقى خفيف) ----------

_light = True


def set_light(value):
    global _light
    _light = bool(value)


def ytdlp_cmd():
    if getattr(sys, "frozen", False):  # نسخة مجمّعة: yt-dlp داخل التطبيق نفسه (run.py --ytdlp)
        exe = shutil.which("yt-dlp")
        return [exe] if exe else [sys.executable, "--ytdlp"]
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        return None


def missing_tools(need_download=False):
    missing = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    if need_download and ytdlp_cmd() is None:
        missing.append("yt-dlp")
    return missing


def check_tools(need_download=False):
    missing = missing_tools(need_download)
    if missing:
        raise EnhanceError("err_tools", tools=", ".join(missing))


def _wrap(cmd):
    """أولوية منخفضة: nice على ماك/لينكس، وBELOW_NORMAL على ويندوز (داخل _popen_kwargs)."""
    if _light and not IS_WIN and shutil.which("nice"):
        return ["nice", "-n", "10", *cmd]
    return list(cmd)


def _popen_kwargs():
    kw = {"env": dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")}
    if IS_WIN:
        flags = 0x08000000  # CREATE_NO_WINDOW: ما تظهر نوافذ سوداء
        if _light:
            flags |= 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
        kw["creationflags"] = flags
    return kw


class CancelToken:
    """رمز إلغاء: cancel() يوقف العمليات الشغّالة لهذي المهمة."""

    def __init__(self):
        self._event = threading.Event()
        self.procs = []

    def is_set(self):
        return self._event.is_set()

    def cancel(self):
        self._event.set()
        for p in list(self.procs):
            try:
                p.terminate()
            except OSError:
                pass

    def check(self):
        if self._event.is_set():
            raise EnhanceError("err_cancelled")


def popen(cmd, token=None, **kw):
    p = subprocess.Popen(_wrap(cmd), encoding="utf-8", errors="replace", **{**_popen_kwargs(), **kw})
    if token is not None:
        token.procs.append(p)
        if token.is_set():
            p.terminate()
    return p


def run(cmd, **kw):
    return subprocess.run(_wrap(cmd), capture_output=True, encoding="utf-8", errors="replace",
                          **{**_popen_kwargs(), **kw})


# ---------- أدوات مساعدة ----------

def is_url(s):
    return str(s).startswith(("http://", "https://"))


def safe_stem(name):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")
    return (s or "song")[:120]


def sub(cb, stage, lo, hi):
    return lambda f: cb(stage, lo + (hi - lo) * max(0.0, min(1.0, f)))


def translate_ytdlp_error(text):
    """يحوّل مخرجات yt-dlp إلى EnhanceError برسالة مفهومة."""
    t = text.lower()
    rules = [
        (("private video", "this video is private"), "err_private"),
        (("video unavailable", "has been removed", "no longer available", "deleted"), "err_unavail"),
        (("sign in", "confirm you", "not a bot", "login required", "age-restricted", "age restricted"), "err_signin"),
        (("unsupported url",), "err_unsupported"),
        (("http error 404", "not found"), "err_404"),
        (("geo", "not available in your country"), "err_geo"),
        (("http error 403", "http error 429"), "err_blocked"),
        (("unable to download", "name or service not known", "timed out", "temporary failure", "connection"), "err_network"),
        (("requested format is not available",), "err_format"),
    ]
    for keys, key in rules:
        if any(k in t for k in keys):
            return EnhanceError(key)
    last = [ln for ln in text.strip().splitlines() if ln.strip() and not ln.startswith(("Deprecated", "WARNING"))]
    return EnhanceError("err_dl", detail=(f": {last[-1][:200]}" if last else "."))


# ---------- التنزيل ----------

def expand_playlist(url):
    """يرجع روابط الأغاني داخل قائمة التشغيل (أو الرابط نفسه لو ما كانت قائمة)."""
    check_tools(need_download=True)
    r = run([*ytdlp_cmd(), "--flat-playlist", "--no-warnings", "--encoding", "utf-8", "--print", "%(url)s", url])
    if r.returncode != 0:
        raise translate_ytdlp_error(r.stderr)
    urls = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().startswith("http")]
    return urls or [url]


def download(url, dest, cb, token=None):
    """ينزّل أعلى جودة صوت بالصيغة الأصلية (بدون تحويل) مع الغلاف والبيانات. يرجع (الملف، الغلاف|None)."""
    cmd = [
        *ytdlp_cmd(), "--no-playlist", "-f", "bestaudio/best", "--encoding", "utf-8",
        "--embed-metadata", "--write-thumbnail", "--convert-thumbnails", "jpg",
        "--newline", "--progress-template", "download:%(progress._percent_str)s",
        "-o", str(Path(dest) / "%(title).120B.%(ext)s"),
        "--print", "after_move:filepath", "--no-simulate", "--no-warnings", url,
    ]
    filepath = None
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        p = popen(cmd, token, stdout=subprocess.PIPE, stderr=err)
        for line in p.stdout:
            line = line.strip()
            m = re.match(r"download:\s*([\d.]+)%", line)
            if m:
                cb(float(m.group(1)) / 100)
            elif line and not line.startswith("download:"):
                filepath = line
        p.wait()
        p.stdout.close()
        err.seek(0)
        errtext = err.read()
    if token is not None:
        token.check()
    if p.returncode != 0:
        raise translate_ytdlp_error(errtext)
    if not filepath or not Path(filepath).exists():
        raise EnhanceError("err_nofile")
    src = Path(filepath)
    thumb = src.with_suffix(".jpg")
    return src, (thumb if thumb.exists() else None)


# ---------- ffmpeg ----------

def run_ffmpeg(args, duration=None, cb=None, token=None, cwd=None):
    """يشغّل ffmpeg مع تقدّم. يرجع نص stderr."""
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        p = popen(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-nostats", "-progress", "pipe:1", *args],
                  token, stdout=subprocess.PIPE, stderr=err, cwd=cwd)
        for line in p.stdout:
            if cb and duration and line.startswith("out_time_us="):
                try:
                    cb(min(int(line.split("=")[1]) / 1e6 / duration, 1.0))
                except ValueError:
                    pass
        p.wait()
        p.stdout.close()
        err.seek(0)
        text = err.read()
    if token is not None:
        token.check()
    if p.returncode != 0:
        tail = [ln for ln in text.strip().splitlines() if ln.strip()][-3:]
        raise EnhanceError("err_ffmpeg", tail=" | ".join(tail))
    return text


def _isnum(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def parse_loudnorm_json(text):
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", text, re.S)
    if not m:
        return None
    try:
        return {k: float(v) if _isnum(v) else v for k, v in json.loads(m.group(0)).items()}
    except ValueError:
        return None


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    if r.returncode != 0:
        raise EnhanceError("err_unreadable")
    j = json.loads(r.stdout)
    streams = j.get("streams", [])
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not audio:
        raise EnhanceError("err_noaudio")
    fmt = j.get("format", {})
    has_video = any(s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic") for s in streams)
    br = int(audio.get("bit_rate") or 0)
    if not br and not has_video:
        br = int(fmt.get("bit_rate") or 0)
    vids = [s for s in streams if s.get("codec_type") == "video"]
    cover_idx = next((i for i, s in enumerate(vids) if s.get("disposition", {}).get("attached_pic")), None)
    return {
        "codec": audio.get("codec_name", "?"),
        "bitrate": br,
        "sample_rate": int(audio.get("sample_rate") or 0),
        "duration": float(fmt.get("duration") or audio.get("duration") or 0),
        "cover_idx": cover_idx,
    }


def analyze(path, duration, cb, token=None):
    """مرور واحد: مستوى الصوت (LUFS) + وجود ترددات فوق 16kHz."""
    fc = ("[0:a]asplit=3[a][b][c];"
          f"[a]{LOUDNORM}:print_format=json[o1];"
          "[b]volumedetect[o2];"
          "[c]highpass=f=16000,volumedetect[o3]")
    text = run_ffmpeg(["-i", str(path), "-filter_complex", fc,
                       "-map", "[o1]", "-f", "null", "-",
                       "-map", "[o2]", "-f", "null", "-",
                       "-map", "[o3]", "-f", "null", "-"], duration, cb, token)
    ln = parse_loudnorm_json(text) or {}
    means = {}
    for m in re.finditer(r"Parsed_volumedetect_(\d+) @ \S+\s+mean_volume:\s*(\S+) dB", text):
        means[int(m.group(1))] = float(m.group(2))
    vals = [means[k] for k in sorted(means)]
    hf_rel = (vals[1] - vals[0]) if len(vals) >= 2 else None
    return {"lufs": ln.get("input_i"), "tp": ln.get("input_tp"), "hf_rel": hf_rel}


def classify(info, hf_rel):
    """تقدير جودة المصدر. تقريبي، ويرجع (المستوى، (مفتاح السبب، معاملاته))."""
    kbps = info["bitrate"] / 1000
    lossless = info["codec"] in LOSSLESS or info["codec"].startswith("pcm")
    hf_missing = hf_rel is not None and hf_rel < -55
    if lossless:
        return "high", ("why_lossless", {})
    if kbps and kbps <= 112:
        return "low", ("why_low_br", {"kbps": f"{kbps:.0f}"})
    if hf_missing:
        return "low", ("why_hf_cut", {})
    if kbps >= 224:
        return "high", ("why_high_br", {"kbps": f"{kbps:.0f}"})
    return "mid", (("why_mid_br", {"kbps": f"{kbps:.0f}"}) if kbps else ("why_mid", {}))


def extract_cover(src, idx, tmp):
    out = Path(tmp) / "cover_embedded.jpg"
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-map", f"0:v:{idx}", "-frames:v", "1", str(out)])
    return out if r.returncode == 0 and out.exists() else None


# ---------- المعالجة الكاملة ----------

# دالة يضبطها الخادم: تحدّث yt-dlp (مرة كل فترة) وترجع True لو حاولت التحديث
_engine_updater = None


def set_engine_updater(fn):
    global _engine_updater
    _engine_updater = fn


ENGINE_RETRY = ("err_dl", "err_format", "err_blocked", "err_signin", "err_unsupported")


def process_item(source, opts, cb=lambda stage, frac: None):
    """
    source: رابط أو مسار ملف.
    opts: preset ('auto' أو اسم نمط)، format، out_dir، name (اختياري)، keep_original (اختياري)، light (اختياري)،
          bass / treble (dB من -6 إلى 6)، token (CancelToken)، original_override (مسار النسخة الأصلية للمقارنة).
    cb(stage_key, frac): تقدّم عام من 0 إلى 1 (stage_key مفتاح في MESSAGES).
    """
    remote = is_url(source)
    check_tools(need_download=remote)
    set_light(opts.get("light", True))
    preset_opt = opts.get("preset", "auto")
    fmt = opts.get("format", "flac")
    out_dir = Path(opts.get("out_dir") or DEFAULT_OUT).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    lufs = opts.get("lufs", -14)
    if lufs not in LUFS_CHOICES:
        lufs = -14
    keep_original = opts.get("keep_original", remote)
    token = opts.get("token")
    bass, treble = int(opts.get("bass", 0) or 0), int(opts.get("treble", 0) or 0)
    extra = ([f"bass=g={bass}:f=110"] if bass else []) + ([f"treble=g={treble}:f=8000"] if treble else [])
    if token:
        token.check()

    with tempfile.TemporaryDirectory(prefix="msga_") as tmpd:
        tmp = Path(tmpd)
        cover = None
        base = 0.0
        if remote:
            cb("st_download", 0.0)
            try:
                src, cover = download(source, tmp, sub(cb, "st_download", 0.0, 0.3), token)
            except EnhanceError as e:
                # فشل التنزيل غالبًا سببه تغيير في الموقع: نحدّث yt-dlp مرة ونعيد المحاولة
                if e.key in ENGINE_RETRY and _engine_updater and _engine_updater():
                    cb("st_engine", 0.0)
                    src, cover = download(source, tmp, sub(cb, "st_download", 0.0, 0.3), token)
                else:
                    raise
            base = 0.3
        else:
            src = Path(source).expanduser().resolve()
            if not src.is_file():
                raise EnhanceError("err_notfound", source=source)

        info = probe(src)
        dur = info["duration"] or None
        if cover is None and info["cover_idx"] is not None:
            cover = extract_cover(src, info["cover_idx"], tmp)

        span = 1.0 - base

        def t(x):
            return base + span * x

        cb("st_analyze", t(0.0))
        an = analyze(src, dur, sub(cb, "st_analyze", t(0.0), t(0.12)), token)
        quality, (reason_key, reason_params) = classify(info, an["hf_rel"])
        auto = preset_opt == "auto"
        preset = AUTO_MAP[quality] if auto else preset_opt
        chain = ",".join(PRESETS[preset] + extra)
        ln = loudnorm_filter(lufs) if lufs else None
        cwd = None
        if "arnndn" in chain:  # موديل الذكاء الاصطناعي: نشغّل ffmpeg داخل مجلد الموديلات ونكتب المسار نسبيًا
            for name in re.findall(r"arnndn=m=([\w.\-]+)", chain):
                if not (MODELS_DIR / name).is_file():
                    raise EnhanceError("err_model", name=name)
            cwd = str(MODELS_DIR)

        if ln:
            # المرحلة 1: قياس بعد الفلاتر عشان التطبيع يكون دقيق
            m = parse_loudnorm_json(run_ffmpeg(
                ["-i", str(src), "-vn", "-af", f"{chain},{ln}:print_format=json", "-f", "null", "-"],
                dur, sub(cb, "st_measure", t(0.12), t(0.45)), token, cwd)) or {}
            keys = ("input_i", "input_lra", "input_tp", "input_thresh", "target_offset")
            if all(isinstance(m.get(k), float) and math.isfinite(m[k]) for k in keys):
                ln2 = (f"{ln}:measured_I={m['input_i']}:measured_LRA={m['input_lra']}"
                       f":measured_TP={m['input_tp']}:measured_thresh={m['input_thresh']}"
                       f":offset={m['target_offset']}:linear=true:print_format=json")
            else:  # ملف صامت أو قياس غير صالح: نرجع للتطبيع المباشر
                ln2 = f"{ln}:print_format=json"
            final_chain = f"{chain},{ln2},alimiter=limit=0.95"
        else:  # بدون تطبيع: نحافظ على مستوى الأغنية، والـ limiter يمنع التشويه فقط
            final_chain = f"{chain},alimiter=limit=0.95"

        stem = safe_stem(opts.get("name") or src.stem)
        suffix = f".{fmt}"
        n = 1
        while True:  # اسم موحّد للمخرجات والنسخة الأصلية بنفس الرقم لو تكرر الاسم
            tag = "" if n == 1 else f" ({n})"
            out = out_dir / f"{stem}{tag}_enhanced{suffix}"
            orig = out_dir / f"{stem}{tag}_original{src.suffix}"
            if not out.exists() and not orig.exists():
                break
            n += 1

        args = ["-i", str(src)]
        if cover and fmt in COVER_FORMATS:
            args += ["-i", str(cover), "-map", "0:a:0", "-map", "1:v", "-c:v", "copy",
                     "-disposition:v", "attached_pic"]
        else:
            args += ["-vn", "-map", "0:a:0"]
        args += ["-map_metadata", "0", "-af", final_chain, *CODECS[fmt], str(out)]
        text = run_ffmpeg(args, dur, sub(cb, "st_process", t(0.45), t(0.97)), token, cwd)
        after = parse_loudnorm_json(text) or {}
        if not ln:  # بدون تطبيع ما فيه قياس جاهز: نقيس الناتج للتقرير
            after = parse_loudnorm_json(run_ffmpeg(
                ["-i", str(out), "-vn", "-af", f"{LOUDNORM}:print_format=json", "-f", "null", "-"],
                dur, None, token)) or {}

        original_path = None
        if keep_original:
            shutil.copy2(src, orig)
            original_path = orig
        elif opts.get("original_override"):
            original_path = Path(opts["original_override"])

    cb("st_done", 1.0)
    return {
        "title": stem,
        "output": str(out),
        "original": str(original_path) if original_path else None,
        "report": {
            "codec": info["codec"], "bitrate_kbps": round(info["bitrate"] / 1000) or None,
            "lossless": info["codec"] in LOSSLESS or info["codec"].startswith("pcm"),
            "hf_rel": an["hf_rel"], "quality": quality,
            "reason": msg(reason_key, "ar", **reason_params),
            "reason_key": reason_key, "reason_params": reason_params,
            "preset": preset, "auto": auto,
            "lufs_before": an["lufs"], "tp_before": an["tp"],
            "lufs_after": after.get("output_i") if ln else after.get("input_i"),
            "tp_after": after.get("output_tp") if ln else after.get("input_tp"),
            "lufs_target": lufs or None, "duration": info["duration"], "format": fmt,
        },
    }


AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".opus", ".wma", ".aiff", ".aif", ".ape", ".mka"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".flv", ".wmv"}  # نأخذ الصوت منها فقط
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS
TAG_KEYS = ("title", "artist", "album")


def collect_media(paths, limit=2000):
    """ملفات اختارها المستخدم + محتوى المجلدات (بشكل متداخل) المفلتر بامتدادات الصوت/الفيديو."""
    out, seen = [], set()
    for raw in paths:
        p = Path(raw).expanduser()
        found = []
        if p.is_file():
            found = [p]
        elif p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for name in sorted(files):
                    if not name.startswith(".") and Path(name).suffix.lower() in MEDIA_EXTS:
                        found.append(Path(root) / name)
        for f in found:
            key = str(f.resolve())
            if key not in seen:
                seen.add(key)
                out.append(Path(key))
            if len(out) >= limit:
                return out
    return out


def read_tags(path):
    """يرجع {title, artist, album, has_cover} لملف صوت."""
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    if r.returncode != 0:
        raise EnhanceError("err_unreadable")
    j = json.loads(r.stdout)
    tags = {k.lower(): v for k, v in (j.get("format", {}).get("tags") or {}).items()}
    for s in j.get("streams", []):
        if s.get("codec_type") == "audio":
            for k, v in (s.get("tags") or {}).items():
                tags.setdefault(k.lower(), v)
    has_cover = any(s.get("codec_type") == "video" for s in j.get("streams", []))
    return {**{k: tags.get(k, "") for k in TAG_KEYS}, "has_cover": has_cover}


def write_tags(path, tags, cover=None):
    """يكتب العنوان/الفنان/الألبوم (ويستبدل الغلاف لو انعطى) بدون إعادة ضغط الصوت. يستبدل الملف بأمان."""
    path = Path(path)
    ext = path.suffix.lower().lstrip(".")
    tmp = path.with_name(f".msga_tmp_{path.name}")
    args = ["-i", str(path)]
    if cover and ext in COVER_FORMATS:
        args += ["-i", str(cover), "-map", "0:a", "-map", "1:v", "-c", "copy", "-disposition:v:0", "attached_pic",
                 "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
    else:
        args += ["-map", "0", "-c", "copy"]
    args += ["-map_metadata", "0"]
    for k in TAG_KEYS:
        if k in tags:
            args += ["-metadata", f"{k}={tags[k]}"]
    if ext == "mp3":
        args += ["-id3v2_version", "3"]
    args.append(str(tmp))
    try:
        run_ffmpeg(args)
        os.replace(tmp, path)
    except EnhanceError:
        raise EnhanceError("err_tags")
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def spectrogram(src, out_png):
    """يرسم طيف الترددات (spectrogram) لملف صوت كصورة PNG."""
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-lavfi",
             "showspectrumpic=s=900x240:legend=0:fscale=log:color=intensity", "-frames:v", "1", str(out_png)])
    if r.returncode != 0 or not Path(out_png).exists():
        tail = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-2:]
        raise EnhanceError("err_ffmpeg", tail=" | ".join(tail))
    return out_png


def clean_old(out_dir, days):
    """يحذف ملفات المخرجات الأقدم من N يوم. يرجع عدد الملفات المحذوفة."""
    out_dir = Path(out_dir)
    if not out_dir.is_dir():
        return 0
    cutoff = time.time() - days * 86400
    n = 0
    for f in out_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            n += 1
    return n


# ---------- خط ثمانية (للعرض في الإعدادات فقط؛ الخط نفسه يحمّله المتصفح من النظام) ----------

def find_thmanyah():
    dirs = [Path.home() / ".local/share/fonts", Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
            Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"),
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"]
    for d in dirs:
        try:
            if d.is_dir():
                for i, f in enumerate(d.rglob("*")):
                    if "thmanyah" in f.name.lower():
                        return True
                    if i > 20000:
                        break
        except OSError:
            continue
    return False
