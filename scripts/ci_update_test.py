"""اختبار آلي كامل للتحديث التلقائي في النسخة المجمّعة (يُشغَّل في CI على ويندوز وماك).

يبني "إصدار 99.0.0" وهمي محليًا، يشغّل نسخة البرنامج المجمّعة، يطلب منها التحديث، ويتأكد أنها نزّلت الملف وتحقّقت
من SHA-256 وأقفلت نفسها واستُبدلت ملفاتها وأعادت التشغيل.
الاستخدام:  python scripts/ci_update_test.py "dist/Make Sound Great Again"   (ماك: ...app)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

IS_MAC = sys.platform == "darwin"
FAKE_PORT = 9911
APP_NAME = "Make Sound Great Again"


def call(port, path, body=None, timeout=300):
    url = f"http://127.0.0.1:{port}{path}"
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def find_port():
    for port in range(8765, 8785):
        try:
            if call(port, "/api/ping", timeout=1).get("app") == APP_NAME:
                return port
        except Exception:
            continue
    return None


def wait_for(cond, seconds, what):
    end = time.time() + seconds
    while time.time() < end:
        v = cond()
        if v:
            return v
        time.sleep(1)
    raise SystemExit(f"TIMEOUT waiting for: {what}")


def kill_all():
    if IS_MAC:
        subprocess.run(["pkill", "-f", APP_NAME], check=False)
    else:
        subprocess.run(["taskkill", "/F", "/IM", f"{APP_NAME}.exe"], check=False, capture_output=True)


work = None


def main():
    dist = Path(sys.argv[1]).resolve()
    global work
    work = Path(tempfile.mkdtemp(prefix="msga_updtest_"))
    os.environ["MSGA_HOME"] = str(work / "home")
    install = work / "install" / dist.name
    shutil.copytree(dist, install, symlinks=True)
    payload = work / "payload" / dist.name
    shutil.copytree(dist, payload, symlinks=True)
    # ويندوز: نضيف ملف علامة للإصدار "الجديد". ماك: ما نعدّل الحزمة (لأن أي تعديل يبطل توقيعها ويمنع تشغيلها)،
    # ونكتشف الاستبدال من تغيّر هوية ملف البرنامج (ditto ينسخ ملفات جديدة).
    marker_rel = Path("UPDATED.txt")
    if not IS_MAC:
        (payload / marker_rel).write_text("updated")

    fake = work / "fake"
    fake.mkdir()
    (fake / "version.py").write_text('VERSION = "99.0.0"\n')
    asset = fake / ("Make-Sound-Great-Again-macos.zip" if IS_MAC else "Make-Sound-Great-Again-windows.zip")
    if IS_MAC:
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(payload), str(asset)], check=True)
    else:
        shutil.make_archive(str(asset.with_suffix("")), "zip", root_dir=payload.parent, base_dir=payload.name)
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    (fake / "SHA256SUMS.txt").write_text(f"{digest}  {asset.name}\n")

    httpd = HTTPServer(("127.0.0.1", FAKE_PORT), partial(SimpleHTTPRequestHandler, directory=str(fake)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    env = dict(os.environ, MSGA_UPDATE_BASE=f"http://127.0.0.1:{FAKE_PORT}", MSGA_HOME=str(work / "home"),
               MSGA_REPO="test/test")
    exe = install / "Contents/MacOS" / APP_NAME if IS_MAC else install / f"{APP_NAME}.exe"
    before = exe.stat().st_ino
    assert not find_port(), "another instance is already running"
    proc = subprocess.Popen([str(exe), "--no-open"], env=env)
    port = wait_for(find_port, 60, "the old app to start")
    info = call(port, "/api/update/check", {})
    assert info.get("available") and info.get("latest") == "99.0.0", info
    print("check ok:", info, flush=True)

    res = call(port, "/api/update/apply", {})
    assert res.get("ok") and res.get("exit"), res
    print("apply ok:", res, flush=True)

    wait_for(lambda: proc.poll() is not None, 60, "the old app to exit")
    print("old app exited", flush=True)
    if IS_MAC:
        wait_for(lambda: exe.exists() and exe.stat().st_ino != before, 120, "the new bundle to replace the old one")
    else:
        wait_for(lambda: (install / marker_rel).exists(), 120, "the new files to be copied over the install folder")
    print("files replaced", flush=True)
    new_port = wait_for(find_port, 90, "the new app to relaunch")
    print("relaunched on port", new_port, flush=True)
    kill_all()
    httpd.shutdown()
    print("UPDATE TEST PASSED")


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:  # noqa: BLE001
        kill_all()
        print("UPDATE TEST FAILED:", repr(e))
        for name in ("app.log", "update/update.log", "update.log"):
            for base in (Path(os.environ.get("MSGA_HOME", "")), Path(os.environ.get("MSGA_HOME", "")) / "update"):
                f = base / Path(name).name
                if f.is_file():
                    print(f"--- {f} ---\n" + f.read_text(errors="replace")[-3000:])
        w = globals().get("work")
        if w:
            for sub in ("home/update", "install"):
                d = Path(w) / sub
                if d.is_dir():
                    print(f"--- ls {d} ---", [p.name for p in d.iterdir()][:30])
        sys.exit(1)
