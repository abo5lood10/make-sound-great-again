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
        core.save_config({**core.load_config(), "out": str(Path(_HOME) / "out")})
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
