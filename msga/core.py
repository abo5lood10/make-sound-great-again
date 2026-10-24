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
                  "lufs": -14, "watch": "", "watch_on": False, "keep_original": False,
                  "auto_player": True, "start_player": False, "mini_corner": "bottom",
                  "trim_silence": True, "tray_close": False, "eq": [0, 0, 0], "crossfade": 0}
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
        "aresample=48000", "arnndn=m=mp.rnnn:mix=0.85",
    ],
    "ai_voice": [  # موديل bd: كلام مع ضوضاء تسجيل (مقاطع تيكتوك / انستا اللي فيها شخص يتكلم)
        "highpass=f=70",
        "aresample=48000", "arnndn=m=bd.rnnn",
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
    "err_nomatch": ("ما لقيت هذي الأغنية في يوتيوب", "Couldn't find this song on YouTube"),
    "err_spotify": ("تعذّر قراءة رابط سبوتيفاي (تأكد إنه رابط أغنية أو ألبوم أو قائمة عامة)",
                    "Couldn't read this Spotify link (it must be a public song, album or playlist)"),
    "err_twitch_sub": ("هذا التسجيل للمشتركين في القناة فقط (Subscriber-only)", "This broadcast is for channel subscribers only"),
    "err_twitch_offline": ("القناة مو مباشرة الحين. الصق رابط تسجيل (VOD) أو مقطع (Clip) من صفحتها",
                           "The channel isn't live right now. Paste a past broadcast (VOD) or clip link from its page"),
    "err_twitch_list": ("هذا رابط صفحة قنوات/تسجيلات وليس تسجيل واحد. افتح التسجيل أو المقطع اللي تبيه والصق رابطه",
                        "This is a channel/list page, not a single broadcast. Open the VOD or clip you want and paste its link"),
    "st_record": ("تسجيل البث المباشر", "Recording the live stream"),
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


# ---------- السجل (آخر 400 سطر، لزر «نسخ السجل» في الإعدادات) ----------
import collections  # noqa: E402

LOG = collections.deque(maxlen=400)


def log(text):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    for line in str(text).rstrip().splitlines() or [""]:
        LOG.append(f"[{stamp}] {line}")


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
    if cfg.get("mini_corner") in ("top", "bottom"):
        out["mini_corner"] = cfg["mini_corner"]
    try:
        eq = [max(-12, min(12, int(v))) for v in cfg.get("eq", [0, 0, 0])][:3]
        out["eq"] = eq + [0] * (3 - len(eq))
    except (TypeError, ValueError):
        pass
    try:
        out["crossfade"] = max(0, min(10, int(cfg.get("crossfade", 0))))
    except (TypeError, ValueError):
        pass
    for key in ("light", "notify", "auto_check", "keep_original", "auto_player", "start_player", "trim_silence",
                "tray_close"):
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


def kill_tree(p):
    """يوقف العملية مع كل عملياتها الفرعية (yt-dlp يشغّل ffmpeg للبث المباشر، وبدون هذا يبقى يسجّل بالخلفية)."""
    try:
        if p.poll() is not None:
            return
        if IS_WIN:
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
        elif getattr(p, "msga_tree", False):
            import signal
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        else:
            p.terminate()
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        try:
            p.terminate()
        except OSError:
            pass


class CancelToken:
    """رمز إلغاء: cancel() يوقف العمليات الشغّالة لهذي المهمة."""

    def __init__(self):
        self._event = threading.Event()
        self.procs = []
        self.stopped = False   # «إيقاف وحفظ»: نوقف التنزيل (بث مباشر) ونكمل بالمعالجة بما تم تسجيله

    def is_set(self):
        return self._event.is_set()

    def stop(self):
        self.stopped = True
        for p in list(self.procs):
            kill_tree(p)

    def cancel(self):
        self._event.set()
        for p in list(self.procs):
            kill_tree(p)

    def check(self):
        if self._event.is_set():
            raise EnhanceError("err_cancelled")


def popen(cmd, token=None, tree=False, **kw):
    """tree=True: العملية تبدأ بمجموعة خاصة (Linux/Mac) عشان نقدر نوقفها مع كل أبنائها."""
    if tree and not IS_WIN:
        kw["start_new_session"] = True
    p = subprocess.Popen(_wrap(cmd), encoding="utf-8", errors="replace", **{**_popen_kwargs(), **kw})
    p.msga_tree = bool(tree and not IS_WIN)
    if token is not None:
        token.procs.append(p)
        if token.is_set():
            kill_tree(p)
    return p


def run(cmd, **kw):
    return subprocess.run(_wrap(cmd), capture_output=True, encoding="utf-8", errors="replace",
                          **{**_popen_kwargs(), **kw})


# ---------- أدوات مساعدة ----------

def is_url(s):
    return str(s).startswith(("http://", "https://"))


_TW = re.compile(r"^https?://(?:(?:www|m|go|player)\.)?twitch\.tv/([^/?#]+)(?:/([^?#]*))?", re.I)
_TW_LIST = {"directory", "videos", "clips", "schedule", "about", "following", "settings", "subscriptions", "wallet", "drops",
            "downloads", "turbo", "friends", "inventory", "jobs", "p", "popout", "embed"}


def twitch_kind(url):
    """نوع رابط تويتش: vod (تسجيل) | clip (مقطع) | live (قناة: بث مباشر) | list (صفحة قنوات/قوائم) | None (مو تويتش)."""
    u = str(url)
    if re.match(r"^https?://clips\.twitch\.tv/[^/?#]+", u, re.I):
        return "clip"
    m = _TW.match(u)
    if not m:
        return None
    first, rest = m.group(1).lower(), (m.group(2) or "").strip("/").lower()
    if first == "videos":
        return "vod" if rest else "list"
    if first in _TW_LIST:
        return "list"
    parts = rest.split("/")
    if parts[0] in ("clip",):
        return "clip" if len(parts) > 1 and parts[1] else "list"
    if parts[0] in ("video", "v", "videos"):
        return "vod" if len(parts) > 1 and parts[1] else "list"
    return "live" if not rest else "list"


def is_remote(s):
    """رابط، أو بحث يوتيوب (ytsearch) نستخدمه لأغاني سبوتيفاي."""
    return is_url(s) or str(s).startswith("ytsearch")


def http_get(url, headers=None, timeout=20):
    """طلب GET بسيط (بدون مكتبات). يرجع bytes."""
    import ssl
    import urllib.request
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MakeSoundGreatAgain)", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def safe_stem(name):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")
    return (s or "song")[:120]


def sub(cb, stage, lo, hi):
    return lambda f: cb(stage, lo + (hi - lo) * max(0.0, min(1.0, f)))


def translate_ytdlp_error(text):
    """يحوّل مخرجات yt-dlp إلى EnhanceError برسالة مفهومة."""
    t = text.lower()
    rules = [
        (("subscriber", "subscribers only", "sub-only"), "err_twitch_sub"),
        (("not currently live", "is offline"), "err_twitch_offline"),
        (("private video", "this video is private"), "err_private"),
        (("video unavailable", "has been removed", "no longer available", "deleted", "does not exist"), "err_unavail"),
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


_NEG_WORDS = ("live", "cover", "remix", "sped up", "speed up", "slowed", "8d", "karaoke", "instrumental", "reaction",
              "nightcore", "reverb", "bass boosted", "mashup", "lofi", "lo-fi", "concert", "acoustic version",
              "مسرع", "ريمكس", "حفلة", "لايف", "كاريوكي", "بطيء")


_AR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"})
_TASHKEEL = re.compile("[\u064B-\u0652\u0640]")
_ALLOWED_EXTRA = {"official", "audio", "video", "hd", "hq", "4k", "remaster", "remastered", "lyrics", "lyric", "music",
                  "feat", "ft", "with", "explicit", "clean", "mv", "visualizer", "من", "فيديو", "كلمات", "حصريا"}


def _norm(text):
    t = _TASHKEEL.sub("", str(text).lower()).translate(_AR)
    return re.sub(r"[^\w\s]", " ", t).split()


def _extra_version_words(cand_title, want_title):
    """كلمات بين أقواس في عنوان النتيجة ما تخص الأغنية (مثل Pianoforte / Acoustic / Live 2019)."""
    want = set(_norm(want_title))
    extra = 0
    for part in re.findall(r"[(\[](.*?)[)\]]", cand_title):
        for w in _norm(part):
            if w not in want and w not in _ALLOWED_EXTRA and not w.isdigit():
                extra += 1
    return extra


def search_youtube_music(query, n=3):
    """أغاني YouTube Music الرسمية (قسم Songs = نسخ شركات الإنتاج، قنوات Topic). العناوين فقط."""
    from urllib.parse import quote_plus
    r = run([*ytdlp_cmd(), "--flat-playlist", "-J", "--no-warnings", "--encoding", "utf-8", "--playlist-items", f"1-{n}",
             f"https://music.youtube.com/search?q={quote_plus(query)}#songs"])
    if r.returncode != 0:
        return []
    try:
        entries = json.loads(r.stdout).get("entries") or []
    except ValueError:
        return []
    return [{"id": e["id"], "title": e.get("title") or "", "channel": "YouTube Music", "duration": None,
             "url": f"https://www.youtube.com/watch?v={e['id']}", "ytm": i + 1}
            for i, e in enumerate(entries) if e.get("id")]


def search_youtube(query, n=10, music=True):
    """نتائج بحث يوتيوب + YouTube Music (بدون تنزيل): [{id, title, channel, duration, url, ytm?}]."""
    check_tools(need_download=True)
    r = run([*ytdlp_cmd(), "--flat-playlist", "-J", "--no-warnings", "--encoding", "utf-8", f"ytsearch{n}:{query}"])
    if r.returncode != 0:
        raise translate_ytdlp_error(r.stderr)
    try:
        entries = json.loads(r.stdout).get("entries") or []
    except ValueError:
        entries = []
    out = search_youtube_music(query) if music else []
    seen = {c["id"] for c in out}
    for e in entries:
        vid = e.get("id")
        if not vid or vid in seen:
            continue
        out.append({"id": vid, "title": e.get("title") or "", "channel": e.get("channel") or e.get("uploader") or "",
                    "duration": e.get("duration"), "url": e.get("url") or f"https://www.youtube.com/watch?v={vid}"})
    return out


def score_candidate(c, title, artist="", duration=None):
    """نقاط لكل نتيجة: النسخة الرسمية (قنوات Topic) أولًا، ونستبعد الحي والريمكس والمسرّع وغيرها."""
    ct, ch = " ".join(_norm(c["title"])), " ".join(_norm(c["channel"]))
    want_t, want_a = _norm(title), _norm(artist)
    score = 0.0
    if c["channel"].endswith(" - Topic"):
        score += 50
    if c.get("ytm"):  # من قسم الأغاني الرسمية في YouTube Music (الأول أقوى)
        score += 42 - 6 * (c["ytm"] - 1)
    if want_a and all(w in ch for w in want_a[:2]):
        score += 15
    if "official audio" in ct:
        score += 12
    elif "official" in ct:
        score += 3
    for w in _NEG_WORDS:
        if w in ct and w not in " ".join(want_t):
            score -= 30
    if "lyrics" in ct or "كلمات" in ct:
        score -= 6
    if "video" in ct or "clip" in ct or "كليب" in ct:
        score -= 4
    if want_t:
        score += 20 * sum(1 for w in want_t if w in ct) / len(want_t)
    score -= min(36, 12 * _extra_version_words(c["title"], title))
    if duration and c.get("duration"):
        diff = abs(float(c["duration"]) - float(duration))
        score += max(0.0, 20 - diff) - (25 if diff > 30 else 0)
    return score


def rank_candidates(cands, title, artist="", duration=None):
    return sorted(cands, key=lambda c: score_candidate(c, title, artist, duration), reverse=True)


def _twitch_audio_variant(master_url):
    """من قائمة البث الرئيسية: رابط نسخة الصوت فقط (audio_only) بدل ما ffmpeg يختار الفيديو."""
    try:
        text = http_get(master_url, timeout=20).decode("utf-8", "replace")
    except Exception:
        return None
    lines = text.splitlines()
    best = None
    for i, ln in enumerate(lines):
        if ln.startswith("#EXT-X-STREAM-INF"):
            nxt = next((x for x in lines[i + 1:] if x.strip() and not x.startswith("#")), None)
            if nxt and ("audio_only" in ln.lower() or ("RESOLUTION" not in ln and "avc1" not in ln)):
                best = nxt.strip()
                break
    return best


def _record_live(url, dest, cb, token, info_cb):
    """يسجّل بث مباشر (تويتش) صوت فقط، مباشرة بـ ffmpeg بصيغة AAC (ما تنكسر لو انقطع التسجيل)."""
    r = run([*ytdlp_cmd(), "--no-warnings", "--encoding", "utf-8", "-f", "audio_only/bestaudio/worst",
             "--print", "%(title).120B", "--print", "%(urls)s", url])
    if r.returncode != 0:
        raise translate_ytdlp_error(r.stderr)
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise EnhanceError("err_nofile")
    title, master = lines[0], lines[-1]
    source = _twitch_audio_variant(master) or master
    out = Path(dest) / (safe_stem(title) + ".aac")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin", "-reconnect", "1", "-reconnect_streamed", "1",
           "-reconnect_delay_max", "5", "-i", source, "-vn", "-map", "0:a:0", "-c:a", "copy", "-f", "adts", str(out)]
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        p = popen(cmd, token, tree=True, stdout=subprocess.DEVNULL, stderr=err)
        while p.poll() is None:
            if info_cb and out.exists():
                info_cb({"bytes": out.stat().st_size})
            time.sleep(1)
        p.wait()
        err.seek(0)
        errtext = err.read()
    if token is not None and not token.stopped:
        token.check()
    if not out.exists() or out.stat().st_size < 4096:
        raise translate_ytdlp_error(errtext) if errtext.strip() else EnhanceError("err_nofile")
    download.last = {"channel": "", "duration": ""}
    return out, None


def download(url, dest, cb, token=None, match_filter=None, live=False, info_cb=None):
    """ينزّل أعلى جودة صوت بالصيغة الأصلية (بدون تحويل) مع الغلاف والبيانات. يرجع (الملف، الغلاف|None)."""
    if live:
        return _record_live(url, dest, cb, token, info_cb)
    cmd = [
        *ytdlp_cmd(), "--no-playlist", "-f", "bestaudio/best", "--encoding", "utf-8",
        "--embed-metadata", "--write-thumbnail", "--convert-thumbnails", "jpg",
        "--newline", "--progress-template", "download:%(progress._percent_str)s|%(progress.downloaded_bytes)s",
        "-o", str(Path(dest) / "%(title).120B.%(ext)s"),
        "--print", "after_move:MSGA\t%(channel)s\t%(duration)s\t%(filepath)s", "--no-simulate", "--no-warnings",
    ]
    if twitch_kind(url):
        cmd += ["--concurrent-fragments", "4", "--retries", "10", "--fragment-retries", "10"]
    searching = str(url).startswith("ytsearch")
    if searching:  # أغاني سبوتيفاي: نأخذ أول نتيجة تنطبق عليها الشروط
        cmd += ["--max-downloads", "1"]
        if match_filter:
            cmd += ["--match-filter", match_filter]
    cmd.append(url)
    filepath = None
    info_out = download.last = {}
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        p = popen(cmd, token, tree=True, stdout=subprocess.PIPE, stderr=err)
        for line in p.stdout:
            line = line.strip()
            m = re.match(r"download:\s*([^|]*)\|(\d*)", line)
            if m:
                pm = re.match(r"\s*([\d.]+)%", m.group(1))
                if pm:
                    cb(float(pm.group(1)) / 100)
                if info_cb and m.group(2):
                    info_cb({"bytes": int(m.group(2))})
            elif line.startswith("MSGA\t"):
                parts = line.split("\t", 3)
                if len(parts) == 4:
                    info_out.update(channel=parts[1], duration=parts[2])
                    filepath = parts[3]
        p.wait()
        p.stdout.close()
        err.seek(0)
        errtext = err.read()
    if token is not None and not token.stopped:
        token.check()
    if token is not None and token.stopped and not token.is_set():
        # «إيقاف وحفظ» لبث مباشر: نأخذ أكبر ملف وسائط انكتب في المجلد
        files = [f for f in Path(dest).iterdir() if f.is_file() and f.suffix.lower() not in (".jpg", ".webp", ".png", ".ytdl", ".part")]
        if not files:
            raise EnhanceError("err_nofile")
        filepath = str(max(files, key=lambda f: f.stat().st_size))
    elif p.returncode not in (0, 101):  # 101 = وصلنا حد --max-downloads (نجاح)
        raise translate_ytdlp_error(errtext)
    if not filepath or not Path(filepath).exists():
        raise EnhanceError("err_nomatch" if searching else "err_nofile")
    src = Path(filepath)
    thumb = src.with_suffix(".jpg")
    return src, (thumb if thumb.exists() else None)


# ---------- ffmpeg ----------

_ERR_WORDS = re.compile(r"error|fail|invalid|no such|cannot|can't|unable|not found|unknown|unsupported|incorrect|"
                        r"unrecognized|not supported|permission|denied|exceed", re.I)


def _ffmpeg_error_summary(text):
    """سطور الخطأ الفعلية من ffmpeg (مو معلومات الملف في الآخر)، وإلا آخر السطور."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    hits = [ln for ln in lines if _ERR_WORDS.search(ln) and not ln.startswith(("Stream #", "Metadata"))]
    return " | ".join((hits[-3:] or lines[-3:]))[:600]


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
        raise EnhanceError("err_ffmpeg", tail=_ffmpeg_error_summary(text))
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


def analyze(path, duration, cb, token=None, limit=None):
    """مرور واحد: مستوى الصوت (LUFS) + وجود ترددات فوق 16kHz."""
    fc = ("[0:a]asplit=3[a][b][c];"
          f"[a]{LOUDNORM}:print_format=json[o1];"
          "[b]volumedetect[o2];"
          "[c]highpass=f=16000,volumedetect[o3]")
    pre = ["-t", str(limit)] if limit else []
    if limit and duration:
        duration = min(duration, limit)
    text = run_ffmpeg([*pre, "-i", str(path), "-filter_complex", fc,
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


LONG_SOURCE_SECONDS = 3600   # أطول من هذا: نحلل عينة، ونطبّع بمرحلة وحدة (والتويتش: lossless يتحول Opus فوق نصفه)
ENGINE_RETRY = ("err_dl", "err_format", "err_blocked", "err_signin", "err_unsupported")


def process_item(source, opts, cb=lambda stage, frac: None):
    """
    source: رابط أو مسار ملف.
    opts: preset ('auto' أو اسم نمط)، format، out_dir، name (اختياري)، keep_original (اختياري)، light (اختياري)،
          bass / treble (dB من -6 إلى 6)، token (CancelToken)، original_override (مسار النسخة الأصلية للمقارنة).
    cb(stage_key, frac): تقدّم عام من 0 إلى 1 (stage_key مفتاح في MESSAGES).
    """
    remote = is_remote(source)
    tw = twitch_kind(source) if is_url(source) else None
    if tw == "list":
        raise EnhanceError("err_twitch_list")
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
        match = None
        if remote:
            cb("st_download", 0.0)
            match = None
            dl_url = source
            if str(source).startswith("ytsearch"):
                # أغنية من سبوتيفاي أو اسم بدون رابط: نرتّب النتائج ونأخذ النسخة الرسمية
                meta = opts.get("meta") or {}
                query = str(source).split(":", 1)[1]
                cands = opts.get("candidates")
                if not cands:
                    dur = (int(opts["duration_ms"]) / 1000) if opts.get("duration_ms") else None
                    cands = rank_candidates(search_youtube(query), meta.get("title") or query, meta.get("artist", ""), dur)
                pick = int(opts.get("pick", 0))
                if pick >= len(cands):
                    raise EnhanceError("err_nomatch")
                match = dict(cands[pick], pick=pick, count=len(cands))
                opts["candidates"] = cands
                dl_url = match["url"]

            def fetch():
                nonlocal dl_url, match
                for attempt in range(3):
                    if tw == "live":
                        cb("st_record", 0.15)
                    got = download(dl_url, tmp, sub(cb, "st_download", 0.0, 0.3), token, None, tw == "live",
                                   opts.get("progress_info"))
                    last = getattr(download, "last", None)
                    info_dl = last if isinstance(last, dict) else {}
                    if match is not None:
                        match.update(channel=info_dl.get("channel") or match.get("channel", ""))
                        want = opts.get("duration_ms")
                        try:
                            real = float(info_dl.get("duration") or 0)
                        except ValueError:
                            real = 0
                        nxt = match["pick"] + 1
                        # مدة مختلفة كثير عن سبوتيفاي: غالبًا نسخة غلط، نجرّب المرشح اللي بعده
                        if want and real and abs(real - int(want) / 1000) > 15 and nxt < len(opts["candidates"]) and attempt < 2:
                            for f in Path(tmp).iterdir():
                                f.unlink()
                            match = dict(opts["candidates"][nxt], pick=nxt, count=len(opts["candidates"]))
                            dl_url = match["url"]
                            continue
                    return got
                return got

            try:
                src, cover = fetch()
            except EnhanceError as e:
                # فشل التنزيل غالبًا سببه تغيير في الموقع: نحدّث yt-dlp مرة ونعيد المحاولة
                if e.key in ENGINE_RETRY and _engine_updater and _engine_updater():
                    cb("st_engine", 0.0)
                    src, cover = fetch()
                else:
                    raise
            base = 0.3
        else:
            src = Path(source).expanduser().resolve()
            if not src.is_file():
                raise EnhanceError("err_notfound", source=source)

        info = probe(src)
        dur = info["duration"] or None
        fmt_note = None
        if tw and fmt in ("flac", "wav") and dur and dur > LONG_SOURCE_SECONDS // 2:
            # صوت تويتش أصلًا مضغوط (AAC)، فالـ FLAC/WAV لبث ساعات بس يضخّم الحجم 5 مرات بدون فايدة
            fmt, fmt_note = "opus", "twitch_opus"
        long_src = bool(dur and dur > LONG_SOURCE_SECONDS)   # ملف طويل: نحلل عينة 10 دقايق، ونطبّع بمرحلة وحدة (أسرع بكثير)
        if cover is None and info["cover_idx"] is not None:
            cover = extract_cover(src, info["cover_idx"], tmp)

        span = 1.0 - base

        def t(x):
            return base + span * x

        cb("st_analyze", t(0.0))
        an = analyze(src, dur, sub(cb, "st_analyze", t(0.0), t(0.12)), token, limit=600 if long_src else None)
        quality, (reason_key, reason_params) = classify(info, an["hf_rel"])
        auto = preset_opt == "auto"
        preset = AUTO_MAP[quality] if auto else preset_opt
        trim = []
        if opts.get("trim_silence") and dur and dur < 20 * 60:
            # صمت حقيقي فقط (أقل من -60dB) ونترك 0.3 ثانية: ما يقص المقدمات الهادئة
            one = "silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.3"
            trim = [one, "areverse", one, "areverse"]
        chain = ",".join(trim + PRESETS[preset] + extra)
        ln = loudnorm_filter(lufs) if lufs else None
        cwd = None
        if "arnndn" in chain:  # موديل الذكاء الاصطناعي: نشغّل ffmpeg داخل مجلد الموديلات ونكتب المسار نسبيًا
            for name in re.findall(r"arnndn=m=([\w.\-]+)", chain):
                if not (MODELS_DIR / name).is_file():
                    raise EnhanceError("err_model", name=name)
            cwd = str(MODELS_DIR)

        if ln and long_src:  # بدون مرحلة قياس: تطبيع ديناميكي بمرحلة وحدة
            final_chain = f"{chain},{ln}:print_format=json,alimiter=limit=0.95"
        elif ln:
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
        args += ["-map_metadata", "0"]
        for k, v in (opts.get("meta") or {}).items():  # بيانات من سبوتيفاي (العنوان / الفنان / الألبوم)
            if k in TAG_KEYS and v:
                args += ["-metadata", f"{k}={v}"]
        args += ["-af", final_chain, *CODECS[fmt], str(out)]
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
            "match": {k: match[k] for k in ("title", "channel", "url", "pick", "count")} if match else None,
            "format_note": fmt_note, "twitch": tw,
        },
        "candidates": opts.get("candidates"),
    }


AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".opus", ".wma", ".aiff", ".aif", ".ape", ".mka"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".flv", ".wmv"}  # نأخذ الصوت منها فقط
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS
TAG_KEYS = ("title", "artist", "album")


PLAYLIST_EXTS = {".m3u", ".m3u8"}


def auto_jobs():
    """أكبر عدد ملفات يقدر الجهاز يعالجها بنفس الوقت (نترك نواة للنظام). مع الأولوية المنخفضة الجهاز يبقى سريع."""
    return max(2, min(8, (os.cpu_count() or 2) - 1))


def read_m3u(path):
    """قائمة تشغيل m3u / m3u8: المسارات (النسبية من مكان الملف) للملفات الموجودة فعلًا."""
    p = Path(path)
    out = []
    try:
        text = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = Path(line) if Path(line).is_absolute() else (p.parent / line)
        if f.is_file() and f.suffix.lower() in MEDIA_EXTS:
            out.append(f)
    return out


def collect_media(paths, limit=2000):
    """ملفات اختارها المستخدم + محتوى المجلدات (بشكل متداخل) المفلتر بامتدادات الصوت/الفيديو + قوائم m3u."""
    out, seen = [], set()
    for raw in paths:
        p = Path(raw).expanduser()
        found = []
        if p.is_file() and p.suffix.lower() in PLAYLIST_EXTS:
            found = read_m3u(p)
        elif p.is_file():
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
    has_cover = any(s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic")
                    for s in j.get("streams", []))  # غلاف فعلي فقط (مو إطار فيديو)
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


# ---------- المشغّل: تحويل مؤقت للصيغ اللي المتصفح ما يشغّلها + أغلفة ----------
BROWSER_SAFE = {"mp3", "m4a", "aac", "wav", "ogg", "opus", "flac", "mp4", "webm", "weba"}


def play_cache_dir():
    d = config_dir() / "play_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_key(path):
    import hashlib
    p = Path(path)
    st = p.stat()
    return hashlib.sha1(f"{p.resolve()}|{st.st_mtime_ns}|{st.st_size}".encode()).hexdigest()[:20]


def transcode_for_play(src):
    """ينسخ الصوت إلى MP3 مؤقت (يقبل Range فيقدر المستخدم يقفز داخل الأغنية). يرجع مسار الملف."""
    out = play_cache_dir() / f"{_cache_key(src)}.mp3"
    if out.exists():
        return out
    tmp = out.with_suffix(".part.mp3")
    run_ffmpeg(["-i", str(src), "-vn", "-map", "0:a:0", "-c:a", "libmp3lame", "-q:a", "3", "-id3v2_version", "3",
                "-map_metadata", "-1", str(tmp)])
    os.replace(tmp, out)
    prune_play_cache()
    return out


def prune_play_cache(max_bytes=1 << 30):
    files = sorted((f for f in play_cache_dir().iterdir() if f.is_file()), key=lambda f: f.stat().st_mtime)
    total = sum(f.stat().st_size for f in files)
    for f in files:
        if total <= max_bytes:
            break
        try:
            total -= f.stat().st_size
            f.unlink()
        except OSError:
            pass


def extract_cover_image(src):
    """غلاف مدمج داخل الملف كصورة jpg (مخزّنة مؤقتًا). يرجع المسار أو None."""
    out = play_cache_dir() / f"{_cache_key(src)}.cover.jpg"
    if out.exists():
        return out if out.stat().st_size else None
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-an", "-map", "0:v:0", "-frames:v", "1", str(out)])
    if r.returncode != 0 or not out.exists():
        out.write_bytes(b"")  # نتذكر إن ما فيه غلاف
        return None
    return out


def media_duration(path):
    try:
        return probe(path)["duration"]
    except EnhanceError:
        return None


def recycle(path):
    """يحذف الملف لسلة المحذوفات في ويندوز (يقدر المستخدم يرجعه). باقي الأنظمة: حذف عادي."""
    p = Path(path)
    if IS_WIN:
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]
        op = SHFILEOPSTRUCTW(None, 3, str(p.resolve()) + "\0", None, 0x0040 | 0x0010 | 0x0004 | 0x0400, False, None, None)
        if ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) != 0 or p.exists():
            raise OSError("recycle failed")
    else:
        p.unlink()


LRCLIB = "https://lrclib.net/api"


def _good_lyrics(d):
    """نتجاهل الإدخالات الناقصة أو التجريبية (مثل سطر واحد «probe»)."""
    synced = [ln for ln in (d.get("syncedLyrics") or "").splitlines() if re.sub(r"\[[^\]]*\]", "", ln).strip()]
    plain = [ln for ln in (d.get("plainLyrics") or "").splitlines() if ln.strip()]
    return len(synced) >= 6 or len(plain) >= 4


def fetch_lyrics(title, artist="", duration=None):
    """كلمات الأغنية من LRCLIB (مجاني ومفتوح، بدون مفتاح). يرجع {synced, plain} أو None."""
    from urllib.parse import urlencode
    from .version import VERSION
    headers = {"User-Agent": f"MakeSoundGreatAgain/{VERSION} (https://github.com/abo5lood10/make-sound-great-again)"}

    def get(url):
        try:
            return json.loads(http_get(url, headers, timeout=12))
        except Exception:
            return None

    def pack(d):
        good_synced = len([ln for ln in (d.get("syncedLyrics") or "").splitlines() if re.sub(r"\[[^\]]*\]", "", ln).strip()]) >= 6
        return {"synced": d.get("syncedLyrics") if good_synced else None, "plain": d.get("plainLyrics")}
    if artist and duration:
        q = urlencode({"track_name": title, "artist_name": artist, "duration": int(round(duration))})
        d = get(f"{LRCLIB}/get?{q}")
        if isinstance(d, dict) and _good_lyrics(d):
            return pack(d)
    res = get(f"{LRCLIB}/search?{urlencode({'q': f'{artist} {title}'.strip()})}") or []
    if not isinstance(res, list):
        return None
    good = [d for d in res[:15] if isinstance(d, dict) and _good_lyrics(d)
            and not (duration and d.get("duration") and abs(d["duration"] - duration) > 8)]
    if not good:
        return None
    # نفضّل المتزامنة، ثم الأقرب بالمدة
    good.sort(key=lambda d: (not d.get("syncedLyrics"), abs((d.get("duration") or 0) - (duration or 0)) if duration else 0))
    return pack(good[0])


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
