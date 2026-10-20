"""تحديث البرنامج من GitHub (بدون أي مكتبات خارجية) + تحديث محرك التنزيل yt-dlp.

- تثبيت من الكود (git / zip): ينسخ ملفات الإصدار الجديد فوق القديمة.
- نسخة جاهزة (exe / app): ينزّل zip الإصدار الجديد، يتحقق من SHA-256، يفكّه، ثم يشغّل سكربت صغير يستبدل ملفات
  البرنامج بعد ما يقفل ويعيد تشغيله (ما يمكن استبدال exe وهو شغّال).
"""
import hashlib
import io
import os
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

from . import core
from .version import GITHUB_REPO, VERSION

FROZEN = bool(getattr(sys, "frozen", False))  # نسخة مجمّعة (exe / app)
PLACEHOLDER = "YOUR_GITHUB_USERNAME"
CHECK_TTL = 6 * 3600
ENGINE_COOLDOWN = 12 * 3600
_check_cache = {"t": 0.0, "value": None}
_engine_last = {"t": 0.0}
SKIP_NAMES = {".git", "__pycache__", ".github"}
ASSET = "Make-Sound-Great-Again-macos.zip" if core.IS_MAC else "Make-Sound-Great-Again-windows.zip"
PROGRESS = {"state": "idle", "done": 0, "total": 0}


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


def _request(url):
    return urllib.request.Request(url, headers={"User-Agent": "MakeSoundGreatAgain-updater"})


def _get(url, timeout=15):
    with urllib.request.urlopen(_request(url), timeout=timeout, context=_ssl_context()) as r:
        return r.read()


def _download(url, dest, timeout=60):
    """تنزيل بالتدريج مع تقدّم. يرجع SHA-256 للملف."""
    h = hashlib.sha256()
    with urllib.request.urlopen(_request(url), timeout=timeout, context=_ssl_context()) as r, open(dest, "wb") as f:
        PROGRESS.update(state="download", done=0, total=int(r.headers.get("Content-Length") or 0))
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
            PROGRESS["done"] += len(chunk)
    return h.hexdigest()


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


def releases_url():
    base = repo_url()
    return f"{base}/releases/latest" if base else None


def _version_url(repo):
    base = os.environ.get("MSGA_UPDATE_BASE")  # للاختبار الآلي فقط
    return f"{base.rstrip('/')}/version.py" if base else f"https://raw.githubusercontent.com/{repo}/main/msga/version.py"


def _asset_base(repo, version):
    base = os.environ.get("MSGA_UPDATE_BASE")
    return f"{base.rstrip('/')}/" if base else f"https://github.com/{repo}/releases/download/v{version}/"


def check(use_cache=False):
    """يرجع {current, latest, available} أو {error}. use_cache: يعيد آخر نتيجة لو أقل من 6 ساعات."""
    if use_cache and _check_cache["value"] and time.time() - _check_cache["t"] < CHECK_TTL:
        return _check_cache["value"]
    out = _check()
    if "error" not in out:
        _check_cache.update(t=time.time(), value=out)
    return out


def _check():
    repo = detect_repo()
    out = {"current": VERSION, "repo": repo, "frozen": FROZEN}
    if PLACEHOLDER in repo:
        out["error"] = "no_repo"
        return out
    try:
        text = _get(_version_url(repo)).decode("utf-8", "replace")
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


def _expected_hash(sums_text, name):
    for line in sums_text.splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m and Path(m.group(2)).name == name:
            return m.group(1).lower()
    return None


# ---------- النسخة الجاهزة (exe / app) ----------

def _ps_quote(text):
    return "'" + str(text).replace("'", "''") + "'"


def _win_script(pid, src, dst, exe):
    """سكربت PowerShell (UTF-8 مع BOM عشان المسارات العربية): ينتظر خروج البرنامج، ينسخ الملفات، ويعيد التشغيل."""
    return "\r\n".join([
        "$ErrorActionPreference = 'Continue'",
        f"$waitPid = {int(pid)}", f"$src = {_ps_quote(src)}", f"$dst = {_ps_quote(dst)}", f"$exe = {_ps_quote(exe)}",
        "$log = Join-Path $PSScriptRoot 'update.log'",
        'function Log($m) { Add-Content -LiteralPath $log -Value ("[{0}] {1}" -f (Get-Date -Format s), $m) -Encoding UTF8 }',
        'Log "waiting for PID $waitPid"',
        "try { Wait-Process -Id $waitPid -Timeout 90 -ErrorAction Stop } catch { Log \"wait: $($_.Exception.Message)\" }",
        "Start-Sleep -Milliseconds 700",
        'Log "copying $src -> $dst"',
        "& robocopy.exe $src $dst /E /NFL /NDL /NJH /NJS /NP /R:20 /W:1 | Out-Null",
        'Log "robocopy exit code $LASTEXITCODE"',
        "Start-Process -FilePath (Join-Path $dst $exe)",
        "Remove-Item -LiteralPath $src -Recurse -Force -ErrorAction SilentlyContinue",
        'Log "done"',
        "Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue", ""])


def _mac_script(pid, src, dst):
    q = shlex.quote
    return "\n".join([
        "#!/bin/bash", f"PID={int(pid)}", f"SRC={q(str(src))}", f"DST={q(str(dst))}",
        'exec >> "$(dirname "$0")/update.log" 2>&1',
        'echo "[$(date)] waiting for PID $PID"',
        'for i in $(seq 1 60); do kill -0 "$PID" 2>/dev/null || break; sleep 1; done',
        'echo "[$(date)] swapping $SRC -> $DST"',
        'rm -rf "$DST.old"; mv "$DST" "$DST.old"',
        'if ditto "$SRC" "$DST"; then rm -rf "$DST.old"; else echo "ditto failed, restoring"; rm -rf "$DST"; mv "$DST.old" "$DST"; fi',
        'xattr -dr com.apple.quarantine "$DST" 2>/dev/null',
        'open "$DST"',
        'echo "[$(date)] done"',
        'rm -rf "$(dirname "$SRC")"; rm -- "$0"', ""])


def apply_frozen():
    info = _check()
    if info.get("error"):
        return {"ok": False, "error": info["error"]}
    if not info.get("available"):
        return {"ok": False, "error": "no_update"}
    repo, latest = detect_repo(), info["latest"]
    try:
        base = _asset_base(repo, latest)
        expected = _expected_hash(_get(base + "SHA256SUMS.txt").decode("utf-8", "replace"), ASSET)
        if not expected:
            return {"ok": False, "error": "bad_checksum"}
        work = core.config_dir() / "update"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        zpath = work / ASSET
        if _download(base + ASSET, zpath) != expected:
            PROGRESS["state"] = "error"
            return {"ok": False, "error": "bad_checksum"}
        PROGRESS["state"] = "extract"
        new = work / "new"
        if core.IS_MAC:
            # ditto يحفظ الروابط الرمزية وصلاحيات التنفيذ (zipfile يفقدها وينكسر التطبيق)
            new.mkdir()
            subprocess.run(["ditto", "-x", "-k", str(zpath), str(new)], check=True)
        else:
            with zipfile.ZipFile(zpath) as zf:
                _safe_extract(zf, new)
        zpath.unlink()
        pid = os.getpid()
        if core.IS_MAC:
            apps = [p for p in new.iterdir() if p.suffix == ".app"]
            target = Path(sys.executable).resolve().parents[2]
            if not apps or target.suffix != ".app":
                return {"ok": False, "error": "bad_archive"}
            script = work / "update.sh"
            script.write_text(_mac_script(pid, apps[0], target), encoding="utf-8")
            script.chmod(0o755)
            subprocess.Popen(["/bin/bash", str(script)], start_new_session=True, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, close_fds=True)
        else:
            dirs = [p for p in new.iterdir() if p.is_dir()]
            payload = dirs[0] if len(dirs) == 1 else new
            exe = Path(sys.executable)
            script = work / "update.ps1"
            script.write_bytes(_win_script(pid, payload, exe.parent, exe.name).encode("utf-8-sig"))
            subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                              "-File", str(script)], creationflags=0x00000008 | 0x00000200,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                             close_fds=True)
        print(f"update: swap script launched ({script})", flush=True)
        PROGRESS["state"] = "ready"
        return {"ok": True, "exit": True, "version": latest}
    except (ValueError, zipfile.BadZipFile, KeyError, subprocess.CalledProcessError):
        PROGRESS["state"] = "error"
        return {"ok": False, "error": "bad_archive"}
    except Exception as e:
        PROGRESS["state"] = "error"
        return {"ok": False, "error": "network", "detail": str(e)[:200]}


# ---------- التثبيت من الكود ----------

def apply():
    """ينزّل آخر نسخة ويستبدل ملفات البرنامج. إعداداتك (خارج مجلد البرنامج) ما تتأثر."""
    repo = detect_repo()
    if PLACEHOLDER in repo:
        return {"ok": False, "error": "no_repo"}
    if FROZEN:
        return apply_frozen()
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


# ---------- محرك التنزيل yt-dlp ----------

def ytdlp_version():
    cmd = core.ytdlp_cmd()
    if not cmd:
        return None
    r = core.run([*cmd, "--version"])
    return r.stdout.strip() if r.returncode == 0 else None


def auto_update_engine():
    """يُستدعى تلقائيًا لما يفشل تنزيل: يحدّث yt-dlp (مرة كل 12 ساعة بحد أقصى). True لو تغيّر الإصدار فعلًا."""
    if time.time() - _engine_last["t"] < ENGINE_COOLDOWN:
        return False
    _engine_last["t"] = time.time()
    res = update_ytdlp()
    return bool(res.get("ok") and res.get("after") and res.get("after") != res.get("before"))


def update_ytdlp():
    """يحدّث yt-dlp (يوتيوب وغيره يغيّرون أشياءهم كثير، فهذا يصلح أغلب أعطال التنزيل)."""
    if FROZEN and not shutil.which("yt-dlp"):
        return {"ok": False, "error": "frozen"}
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
