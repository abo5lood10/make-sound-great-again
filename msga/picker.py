"""نوافذ اختيار ملفات/مجلدات من نظام التشغيل نفسه (بدون مكتبات): zenity/kdialog على Linux،
osascript على ماك، PowerShell على ويندوز. تُشغَّل في عملية منفصلة عشان ما تعطّل نافذة البرنامج."""
import shutil
import subprocess

from . import core

TITLE_FILES = "Make Sound Great Again"


def available():
    if core.IS_WIN or core.IS_MAC:
        return True
    return bool(shutil.which("zenity") or shutil.which("kdialog"))


def _run(cmd, timeout=3600):
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
                       **({"creationflags": 0x08000000} if core.IS_WIN else {}))
    return r


def pick(kind):
    """kind: 'files' أو 'folder'. يرجع قائمة مسارات (فاضية لو المستخدم ألغى) أو None لو ما فيه نافذة اختيار."""
    if core.IS_WIN:
        return _pick_windows(kind)
    if core.IS_MAC:
        return _pick_mac(kind)
    return _pick_linux(kind)


def _lines(text):
    return [ln.strip() for ln in text.replace("\r", "").split("\n") if ln.strip()]


def _pick_windows(kind):
    exts = ";".join(f"*{e}" for e in sorted(core.MEDIA_EXTS))
    if kind == "folder":
        body = ("$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath }")
    else:
        body = ("$d = New-Object System.Windows.Forms.OpenFileDialog; $d.Multiselect = $true; "
                f"$d.Filter = 'Audio / video|{exts}|All files|*.*'; "
                "if ($d.ShowDialog() -eq 'OK') { $d.FileNames -join \"`n\" }")
    ps = ("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
          "Add-Type -AssemblyName System.Windows.Forms; " + body)
    r = _run(["powershell", "-NoProfile", "-STA", "-Command", ps])
    return _lines(r.stdout)


def _pick_mac(kind):
    if kind == "folder":
        script = ['POSIX path of (choose folder with prompt "Choose a folder")']
    else:
        script = ['set f to choose file with prompt "Choose songs" with multiple selections allowed',
                  'set out to ""', 'repeat with i in f', 'set out to out & POSIX path of i & linefeed', 'end repeat',
                  'return out']
    cmd = ["osascript"]
    for line in script:
        cmd += ["-e", line]
    r = _run(cmd)
    return _lines(r.stdout) if r.returncode == 0 else []  # الإلغاء يرجع خطأ -128


def _pick_linux(kind):
    if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", "--multiple", "--separator=\n", f"--title={TITLE_FILES}"]
        if kind == "folder":
            cmd.append("--directory")
        return _lines(_run(cmd).stdout)
    if shutil.which("kdialog"):
        cmd = (["kdialog", "--getexistingdirectory", "."] if kind == "folder"
               else ["kdialog", "--getopenfilename", ".", "--multiple", "--separate-output"])
        return _lines(_run(cmd).stdout)
    return None
