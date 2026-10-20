import http.client
import io
import json
import os
import shutil
import string
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_HOME = tempfile.mkdtemp(prefix="msga_test_home_")
os.environ["MSGA_HOME"] = _HOME

from msga import core, server, updater  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def make_tone(path, bitrate="64k"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=440:d=4",
                    "-f", "lavfi", "-i", "anoisesrc=d=4:a=0.05", "-filter_complex", "amix=inputs=2",
                    "-c:a", "libmp3lame", "-b:a", bitrate, str(path)], check=True)


def make_png(path, color="red"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={color}:s=96x96",
                    "-frames:v", "1", str(path)], check=True)


class Basics(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(updater.parse_version("v1.2.3"), (1, 2, 3))
        self.assertTrue(updater.is_newer("1.10.0", "1.9.9"))
        self.assertFalse(updater.is_newer("1.0.0", "1.0.0"))
        self.assertFalse(updater.is_newer("0.9", "1.0.0"))

    def test_config_roundtrip_and_sanitize(self):
        core.save_config({"lang": "en", "theme": "dark", "jobs": 99, "preset": "bogus", "light": False})
        cfg = core.load_config()
        self.assertEqual((cfg["lang"], cfg["theme"], cfg["jobs"], cfg["preset"], cfg["light"]),
                         ("en", "dark", 8, "auto", False))

    def test_all_messages_are_bilingual_and_formattable(self):
        for key, (ar, en) in core.MESSAGES.items():
            self.assertTrue(ar and en, key)
            names = {f for text in (ar, en) for _, f, _, _ in string.Formatter().parse(text) if f}
            for lang in ("ar", "en"):
                core.msg(key, lang, **{n: "x" for n in names})

    def test_safe_stem(self):
        self.assertEqual(core.safe_stem('a/b:c*?"<>|'), "a_b_c______")
        self.assertEqual(core.safe_stem("  .. "), "song")

    def test_classify(self):
        self.assertEqual(core.classify({"bitrate": 64000, "codec": "mp3"}, None)[0], "low")
        self.assertEqual(core.classify({"bitrate": 320000, "codec": "mp3"}, -20)[0], "high")
        self.assertEqual(core.classify({"bitrate": 0, "codec": "flac"}, None)[0], "high")
        self.assertEqual(core.classify({"bitrate": 160000, "codec": "aac"}, -70)[0], "low")

    def test_ytdlp_error_translation(self):
        self.assertEqual(core.translate_ytdlp_error("ERROR: Private video").key, "err_private")
        self.assertEqual(core.translate_ytdlp_error("HTTP Error 404: Not Found").key, "err_404")
        self.assertEqual(core.translate_ytdlp_error("something odd").key, "err_dl")


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class Processing(unittest.TestCase):
    def test_process_local_file(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "in.mp3", Path(d) / "out"
            make_tone(src)
            stages = []
            res = core.process_item(str(src), {"preset": "auto", "format": "flac", "out_dir": str(out)},
                                    lambda s, f: stages.append(s))
            self.assertTrue(Path(res["output"]).is_file())
            self.assertTrue(res["output"].endswith("_enhanced.flac"))
            self.assertIsNone(res["original"])  # الملف المحلي ما ينسخ
            r = res["report"]
            self.assertEqual(r["quality"], "low")
            self.assertEqual(r["preset"], "clean")
            self.assertAlmostEqual(r["lufs_after"], -14.0, delta=1.5)
            self.assertIn("st_analyze", stages)
            codec = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of",
                                    "csv=p=0", res["output"]], capture_output=True, text=True).stdout.strip()
            self.assertEqual(codec, "flac")

    def test_mp3_output_and_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.mp3"
            make_tone(src)
            res = core.process_item(str(src), {"preset": "bass", "format": "mp3", "out_dir": d})
            self.assertTrue(res["output"].endswith(".mp3"))
            with self.assertRaises(core.EnhanceError) as ctx:
                core.process_item(str(Path(d) / "nope.mp3"), {"out_dir": d})
            self.assertEqual(ctx.exception.key, "err_notfound")


class ServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core.save_config({**core.load_config(), "out": str(Path(_HOME) / "out"), "notify": False})
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, data

    def test_basics_and_security(self):
        self.assertEqual(self.req("GET", "/api/ping")[0], 200)
        self.assertEqual(self.req("GET", "/")[0], 200)
        self.assertEqual(self.req("GET", "/static/fonts/Audiowide-Regular.ttf")[0], 200)
        self.assertEqual(self.req("GET", "/static/../core.py")[0], 404)
        self.assertEqual(self.req("GET", "/api/ping", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.req("POST", "/api/clear", body=b"{}", headers={"Origin": "http://evil.example"})[0], 403)
        st = json.loads(self.req("GET", "/api/state")[1])
        self.assertEqual(st["version"], updater.VERSION)
        self.assertIn("missing", st)

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
    def test_upload_process_and_range(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "song.mp3"
            make_tone(src)
            status, _ = self.req("POST", "/api/upload?name=song.mp3&preset=auto&format=flac", body=src.read_bytes())
            self.assertEqual(status, 200)
        item = None
        for _ in range(120):
            items = json.loads(self.req("GET", "/api/state")[1])["items"]
            item = next((i for i in items if i["label"] == "song.mp3"), None)
            if item and item["status"] in ("done", "error"):
                break
            time.sleep(0.5)
        self.assertEqual(item["status"], "done", item)
        url = item["result"]["output_url"]
        status, data = self.req("GET", url, headers={"Range": "bytes=0-99"})
        self.assertEqual((status, len(data)), (206, 100))
        self.assertEqual(list(core.upload_dir().iterdir()), [])  # الملف المرفوع انحذف


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class Features(unittest.TestCase):
    def test_all_formats(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.mp3"
            make_tone(src)
            for fmt in core.CODECS:
                if fmt == "opus" and "libopus" not in subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                                                                      capture_output=True, text=True).stdout:
                    continue
                res = core.process_item(str(src), {"format": fmt, "out_dir": d, "bass": 3, "treble": -2})
                self.assertTrue(res["output"].endswith("." + fmt))
                self.assertGreater(Path(res["output"]).stat().st_size, 1000, fmt)

    def test_cancel(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.mp3"
            make_tone(src)
            token = core.CancelToken()
            token.cancel()
            with self.assertRaises(core.EnhanceError) as ctx:
                core.process_item(str(src), {"out_dir": d, "token": token})
            self.assertEqual(ctx.exception.key, "err_cancelled")

    def test_spectrogram(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.mp3"
            make_tone(src)
            png = core.spectrogram(src, Path(d) / "s.png")
            self.assertGreater(Path(png).stat().st_size, 1000)

    def test_engine_update_retry(self):
        calls = []
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(core, "download", side_effect=[core.EnhanceError("err_dl", detail=""),
                                                                 (Path(d) / "x.mp3", None)]) as dl:
            make_tone(Path(d) / "x.mp3")
            core.set_engine_updater(lambda: calls.append(1) or True)
            try:
                core.process_item("https://example.com/x", {"out_dir": d})
            finally:
                core.set_engine_updater(None)
            self.assertEqual(dl.call_count, 2)
            self.assertEqual(calls, [1])

    def test_no_engine_retry_for_private_video(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(core, "download", side_effect=core.EnhanceError("err_private")) as dl:
            core.set_engine_updater(lambda: True)
            try:
                with self.assertRaises(core.EnhanceError):
                    core.process_item("https://example.com/x", {"out_dir": d})
            finally:
                core.set_engine_updater(None)
            self.assertEqual(dl.call_count, 1)


class ServerFeatures(unittest.TestCase):
    """يشغّل الخادم بحالة نظيفة ويفحص الإلغاء والسجل والمعالجة المتكررة."""

    @classmethod
    def setUpClass(cls):
        core.save_config({**core.load_config(), "out": str(Path(_HOME) / "out2"), "notify": False})
        server.STATE.items.clear()
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def call(self, method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        c.request(method, path, body=data)
        r = c.getresponse()
        raw = r.read()
        c.close()
        return r.status, raw

    def items(self):
        return json.loads(self.call("GET", "/api/state")[1])["items"]

    def wait(self, pred, tries=120):
        for _ in range(tries):
            hit = next((i for i in self.items() if pred(i)), None)
            if hit:
                return hit
            time.sleep(0.5)
        self.fail("timeout")

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
    def test_reprocess_history_and_spectrogram(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "feat.mp3"
            make_tone(src)
            self.call("POST", "/api/upload?name=feat.mp3&preset=auto&format=flac", src.read_bytes())
        first = self.wait(lambda i: i["label"] == "feat.mp3" and i["status"] == "done")
        self.assertTrue(first["can_rerun"])
        st, png = self.call("GET", f"/api/spectrogram?id={first['id']}&which=e")
        self.assertEqual((st, png[:4]), (200, b"\x89PNG"))
        st, _ = self.call("POST", "/api/reprocess", {"id": first["id"], "preset": "bass", "format": "mp3", "bass": 2})
        self.assertEqual(st, 200)
        again = self.wait(lambda i: i["id"] != first["id"] and i["label"] == "feat.mp3" and i["status"] == "done")
        self.assertTrue(again["result"]["output_url"].endswith(".mp3"))
        self.assertTrue(again["result"]["original_url"])  # المقارنة تبقى متاحة
        hist = json.loads(server.history_path().read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(hist), 2)
        # السجل يرجع بعد "إعادة التشغيل"
        server.STATE.items.clear()
        server.load_history()
        self.assertGreaterEqual(len(self.items()), 2)

    def test_cancel_and_retry(self):
        it = server.STATE.new_item("x", "file", source="/nonexistent.mp3",
                                   opts={"preset": "auto", "format": "flac", "out_dir": _HOME, "light": True})
        it["_token"].cancel()
        self.assertEqual(self.call("POST", "/api/cancel", {"id": it["id"]})[0], 200)
        server.run_item(it)  # الإلغاء قبل البدء يعطي حالة cancelled
        self.assertEqual(it["status"], "cancelled")
        self.assertFalse(public_retry(it))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class LocalFilesAndWatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg_out = str(Path(_HOME) / "out3")
        core.save_config({**core.load_config(), "out": cls.cfg_out, "notify": False, "watch": "", "watch_on": False})
        server.STATE.items.clear()
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def call(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        c.request(method, path, body=data, headers=headers or {})
        r = c.getresponse()
        raw = r.read()
        c.close()
        return r.status, raw

    def wait_done(self, label, tries=120):
        for _ in range(tries):
            items = json.loads(self.call("GET", "/api/state")[1])["items"]
            hit = next((i for i in items if i["label"] == label and i["status"] in ("done", "error")), None)
            if hit:
                return hit
            time.sleep(0.5)
        self.fail("timeout")

    def test_folder_processing_original_stays_and_serves(self):
        folder = Path(tempfile.mkdtemp())
        make_tone(folder / "local_song.mp3")
        st, _ = self.call("POST", "/api/submit_paths", {"paths": [str(folder)]})
        self.assertEqual(st, 200)
        it = self.wait_done("local_song.mp3")
        self.assertEqual(it["status"], "done", it)
        self.assertTrue((folder / "local_song.mp3").is_file())          # الأصل ما انحذف ولا انتقل
        self.assertFalse(list(Path(self.cfg_out).glob("*_original*")))  # وما انعمل له نسخة
        self.assertTrue(it["result"]["original_url"].startswith("/orig/"))
        st, data = self.call("GET", it["result"]["original_url"], headers={"Range": "bytes=0-9"})
        self.assertEqual((st, len(data)), (206, 10))
        # تاغات + غلاف عبر الـ API
        st, raw = self.call("POST", "/api/tags", {"id": it["id"], "title": "T", "artist": "A", "album": "B"})
        self.assertEqual(st, 200)
        tags = json.loads(self.call("GET", f"/api/tags?id={it['id']}")[1])
        self.assertEqual((tags["title"], tags["artist"], tags["album"]), ("T", "A", "B"))
        png = Path(tempfile.mkdtemp()) / "c.png"
        make_png(png)
        st, _ = self.call("POST", f"/api/cover?id={it['id']}", png.read_bytes())
        self.assertEqual(st, 200)
        self.assertTrue(json.loads(self.call("GET", f"/api/tags?id={it['id']}")[1])["has_cover"])
        st, _ = self.call("POST", f"/api/cover?id={it['id']}", b"not an image")
        self.assertEqual(st, 400)

    def test_watch_folder_only_processes_new_files(self):
        folder = Path(tempfile.mkdtemp())
        make_tone(folder / "old_song.mp3")
        core.save_config({**core.load_config(), "watch": str(folder), "watch_on": True})
        before = len(server.STATE.items)
        server.watch_scan()                                  # أول دورة: خط أساس فقط، ما يعالج الموجود
        self.assertEqual(len(server.STATE.items), before)
        make_tone(folder / "new_song.mp3")
        past = time.time() - 60
        os.utime(folder / "new_song.mp3", (past, past))
        server.watch_scan()                                  # يسجّل الحجم
        server.watch_scan()                                  # حجمه ثابت: يعالجه
        labels = [i["label"] for i in server.STATE.items[before:]]
        self.assertEqual(labels, ["new_song.mp3"])
        it = self.wait_done("new_song.mp3")
        self.assertEqual(it["status"], "done", it)
        self.assertEqual(server.watch_scan(), 0)             # ما يعيده
        core.save_config({**core.load_config(), "watch": "", "watch_on": False})


def public_retry(it):
    return server.public(it)["can_retry"]


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class Quality(unittest.TestCase):
    """فحوص موضوعية لسلامة الصوت (ما تقدر تقيّم الذوق، لكنها تمنع التشويه وأخطاء المستوى)."""

    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp())
        cls.src = cls.dir / "music.mp3"
        make_tone(cls.src, "128k")

    def run_preset(self, **kw):
        opts = {"out_dir": str(self.dir / "o"), "format": "flac"}
        opts.update(kw)
        return core.process_item(str(self.src), opts)["report"]

    def test_loudness_targets_are_hit_without_clipping(self):
        for target in (-16, -14, -11, -9):
            r = self.run_preset(lufs=target)
            self.assertAlmostEqual(r["lufs_after"], target, delta=1.0, msg=f"target {target}")
            self.assertLessEqual(r["tp_after"], -0.5, f"true peak at {target}")

    def test_no_normalization_keeps_level_and_never_clips(self):
        r = self.run_preset(lufs=0)
        self.assertLessEqual(r["tp_after"], 0.0)
        self.assertAlmostEqual(r["lufs_after"], r["lufs_before"], delta=3.0)

    def test_every_preset_is_safe(self):
        for preset in core.PRESETS:
            r = self.run_preset(preset=preset)
            self.assertLessEqual(r["tp_after"], -0.5, preset)
            self.assertAlmostEqual(r["lufs_after"], -14.0, delta=1.5, msg=preset)

    def test_ai_presets_need_their_models(self):
        with mock.patch.object(core, "MODELS_DIR", Path(tempfile.mkdtemp())):
            with self.assertRaises(core.EnhanceError) as ctx:
                self.run_preset(preset="ai_music")
            self.assertEqual(ctx.exception.key, "err_model")

    def test_tags_and_cover_roundtrip(self):
        out = core.process_item(str(self.src), {"out_dir": str(self.dir / "t"), "format": "flac"})["output"]
        core.write_tags(out, {"title": "عنوان", "artist": "Artist", "album": "Album"})
        tags = core.read_tags(out)
        self.assertEqual((tags["title"], tags["artist"], tags["album"]), ("عنوان", "Artist", "Album"))
        img = self.dir / "c.png"
        make_png(img, "blue")
        core.write_tags(out, {}, cover=img)
        self.assertTrue(core.read_tags(out)["has_cover"])
        self.assertEqual(core.read_tags(out)["title"], "عنوان")  # التاغات تبقى

    def test_collect_media_filters_and_recurses(self):
        root = Path(tempfile.mkdtemp())
        (root / "sub").mkdir()
        for name in ("a.mp3", "sub/b.FLAC", "sub/c.txt", "d.mp4", ".hidden.mp3"):
            (root / name).write_bytes(b"x")
        names = sorted(p.name for p in core.collect_media([str(root)]))
        self.assertEqual(names, ["a.mp3", "b.FLAC", "d.mp4"])


class Startup(unittest.TestCase):
    def test_starts_with_legacy_windows_console_encoding(self):
        """ويندوز: طرفية cp1252 ما تقدر تكتب حروف مثل السهم، والبرنامج ما لازم ينهار منها."""
        env = dict(os.environ, PYTHONIOENCODING="cp1252", MSGA_HOME=tempfile.mkdtemp(), MSGA_PORT="8840")
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent.parent / "run.py"), "--no-open"],
                             env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            time.sleep(3)
            self.assertIsNone(p.poll(), p.stderr.read().decode(errors="replace") if p.poll() is not None else "")
        finally:
            p.terminate()
            p.wait(timeout=10)
            p.stdout.close()
            p.stderr.close()


class FrozenUpdateHelpers(unittest.TestCase):
    def test_expected_hash_parsing(self):
        sums = "a" * 64 + "  other.zip\n" + "b" * 64 + "  *Make-Sound-Great-Again-windows.zip\n"
        self.assertEqual(updater._expected_hash(sums, "Make-Sound-Great-Again-windows.zip"), "b" * 64)
        self.assertIsNone(updater._expected_hash(sums, "missing.zip"))

    def test_windows_script_has_all_parts(self):
        text = updater._win_script(321, r"C:\new\App", r"C:\Users\Me\My App", "App.exe")
        for needle in ('set "PID=321"', r'set "SRC=C:\new\App"', r'set "DST=C:\Users\Me\My App"', "robocopy",
                       'start "" "%DST%\\%EXE%"', "tasklist"):
            self.assertIn(needle, text)

    @unittest.skipIf(os.name == "nt", "bash script")
    def test_mac_script_swaps_bundle_and_relaunches(self):
        root = Path(tempfile.mkdtemp())
        (root / "bin").mkdir()
        src, dst = root / "src" / "New App.app", root / "dst" / "My App.app"
        for d, text in ((src, "new"), (dst, "old")):
            (d / "Contents").mkdir(parents=True)
            (d / "Contents" / "v.txt").write_text(text)
        shims = {"ditto": 'cp -a "$1" "$2"', "open": f'touch "{root}/opened"', "xattr": "exit 0"}
        for name, body in shims.items():
            (root / "bin" / name).write_text("#!/bin/bash\n" + body + "\n")
            (root / "bin" / name).chmod(0o755)
        script = root / "u.sh"
        script.write_text(updater._mac_script(999999, src, dst))
        subprocess.run(["bash", str(script)], check=True, env=dict(os.environ, PATH=f"{root / 'bin'}:{os.environ['PATH']}"))
        self.assertEqual((dst / "Contents" / "v.txt").read_text(), "new")
        self.assertTrue((root / "opened").exists())
        self.assertFalse((root / "src").exists())


class Updater(unittest.TestCase):
    def _zip(self, version, extra=None):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("repo-main/msga/version.py", f'VERSION = "{version}"\n')
            z.writestr("repo-main/new.txt", "hello")
            for name, content in (extra or {}).items():
                z.writestr(name, content)
        return buf.getvalue()

    def test_check(self):
        with mock.patch.object(updater, "detect_repo", return_value="me/repo"), \
                mock.patch.object(updater, "_get", return_value=b'VERSION = "9.0.0"\n'):
            r = updater.check()
        self.assertTrue(r["available"])
        self.assertEqual(r["latest"], "9.0.0")

    def test_check_without_repo(self):
        with mock.patch.object(updater, "detect_repo", return_value="YOUR_GITHUB_USERNAME/x"):
            self.assertEqual(updater.check()["error"], "no_repo")

    def test_apply_copies_files(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(core, "ROOT", Path(d)), \
                mock.patch.object(updater, "detect_repo", return_value="me/repo"), \
                mock.patch.object(updater, "_get", return_value=self._zip("9.9.9")):
            r = updater.apply()
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["version"], "9.9.9")
            self.assertEqual((Path(d) / "new.txt").read_text(), "hello")
            self.assertTrue((Path(d) / "msga" / "version.py").is_file())

    def test_apply_rejects_zip_slip(self):
        evil = self._zip("9.9.9", {"../evil.txt": "x"})
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(core, "ROOT", Path(d)), \
                mock.patch.object(updater, "detect_repo", return_value="me/repo"), \
                mock.patch.object(updater, "_get", return_value=evil):
            r = updater.apply()
            self.assertFalse(r["ok"])
            self.assertFalse((Path(d).parent / "evil.txt").exists())


if __name__ == "__main__":
    unittest.main()
