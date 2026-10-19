"""تحديث البرنامج من GitHub (بدون أي مكتبات خارجية) + تحديث محرك التنزيل yt-dlp."""
import io
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from . import core
from .version import GITHUB_REPO, VERSION

PLACEHOLDER = "YOUR_GITHUB_USERNAME"
SKIP_NAMES = {".git", "__pycache__", ".github"}


def parse_version(s):
    """'1.2.3' -> (1, 2, 3). يتجاهل أي لاحقة مثل v أو -beta."""
    nums = re.findall(r"\d+", str(s).split("-")[0])
    return tuple(int(n) for n in nums[:4]) or (0,)


def is_newer(latest, current=VERSION):
    return parse_version(latest) > parse_version(current)


def _ssl_context():
    try:
        import certifi  # اختياري: يحل مشكلة الشهادات في بايثون على ماك
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "MakeSoundGreatAgain-updater"})
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
        return r.read()


def detect_repo():
    """owner/name: من git remote لو التطبيق منسوخ بـ git، وإلا من الثابت في version.py (أو MSGA_REPO)."""
    env = os.environ.get("MSGA_REPO")
    if env:
        return env
    if (core.ROOT / ".git").exists() and shutil.which("git"):
        r = subprocess.run(["git", "-C", str(core.ROOT), "remote", "get-url", "origin"],
                           capture_output=True, text=True)
        m = re.search(r"github\.com[:/]+([^/\s]+/[^/\s]+?)(?:\.git)?\s*$", r.stdout.strip())
        if r.returncode == 0 and m:
            return m.group(1)
    return GITHUB_REPO


def repo_url():
    repo = detect_repo()
    return None if PLACEHOLDER in repo else f"https://github.com/{repo}"


def check():
    """يرجع {current, latest, available} أو {error} (رسالة خطأ بالمفتاح)."""
    repo = detect_repo()
    out = {"current": VERSION, "repo": repo}
    if PLACEHOLDER in repo:
        out["error"] = "no_repo"
        return out
    try:
        text = _get(f"https://raw.githubusercontent.com/{repo}/main/msga/version.py").decode("utf-8", "replace")
        m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', text, re.M)
        if not m:
            raise ValueError("version not found")
        out["latest"] = m.group(1)
        out["available"] = is_newer(m.group(1))
    except Exception:
        out["error"] = "network"
    return out


def _safe_extract(zf, dest):
    dest = Path(dest).resolve()
    for member in zf.namelist():
        target = (dest / member).resolve()
        if dest != target and dest not in target.parents:  # حماية من zip-slip
            raise ValueError("unsafe path in archive")
    zf.extractall(dest)


def apply():
    """ينزّل آخر نسخة ويستبدل ملفات البرنامج. إعداداتك (خارج مجلد البرنامج) ما تتأثر."""
    repo = detect_repo()
    if PLACEHOLDER in repo:
        return {"ok": False, "error": "no_repo"}
    try:
        if (core.ROOT / ".git").exists() and shutil.which("git"):
            r = subprocess.run(["git", "-C", str(core.ROOT), "pull", "--ff-only"], capture_output=True, text=True)
            if r.returncode != 0:
                return {"ok": False, "error": "git", "detail": (r.stderr or r.stdout).strip()[-300:]}
            return {"ok": True, "restart": True}
        data = _get(f"https://github.com/{repo}/archive/refs/heads/main.zip", timeout=60)
        with tempfile.TemporaryDirectory(prefix="msga_upd_") as tmp, zipfile.ZipFile(io.BytesIO(data)) as zf:
            _safe_extract(zf, tmp)
            tops = [p for p in Path(tmp).iterdir() if p.is_dir()]
            top = tops[0] if len(tops) == 1 else Path(tmp)
            ver_file = top / "msga" / "version.py"
            m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', ver_file.read_text(encoding="utf-8"), re.M)
            if not m:
                return {"ok": False, "error": "bad_archive"}
            for src in top.rglob("*"):
                rel = src.relative_to(top)
                if src.is_dir() or SKIP_NAMES & set(rel.parts):
                    continue
                dst = core.ROOT / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            return {"ok": True, "restart": True, "version": m.group(1)}
    except (ValueError, zipfile.BadZipFile, KeyError):
        return {"ok": False, "error": "bad_archive"}
    except Exception as e:
        return {"ok": False, "error": "network", "detail": str(e)[:200]}


def ytdlp_version():
    cmd = core.ytdlp_cmd()
    if not cmd:
        return None
    r = core.run([*cmd, "--version"])
    return r.stdout.strip() if r.returncode == 0 else None


def update_ytdlp():
    """يحدّث yt-dlp (يوتيوب وغيره يغيّرون أشياءهم كثير، فهذا يصلح أغلب أعطال التنزيل)."""
    try:
        import yt_dlp  # noqa: F401
        pip_installed = True
    except ImportError:
        pip_installed = False
    before = ytdlp_version()
    if pip_installed:
        r = core.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
    else:
        cmd = core.ytdlp_cmd()
        if not cmd:
            return {"ok": False, "error": "no_ytdlp"}
        r = core.run([*cmd, "-U"])
    after = ytdlp_version()
    return {"ok": r.returncode == 0, "before": before, "after": after,
            "detail": (r.stderr or r.stdout).strip()[-200:] if r.returncode else ""}
