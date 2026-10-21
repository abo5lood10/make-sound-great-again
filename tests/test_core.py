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

from msga import core, fontpack, server, spotify, updater, winctl  # noqa: E402

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
        core.save_config({**core.load_config(), "out": str(Path(_HOME) / "out2"), "notify": False,
                          "keep_original": True})
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
            # نماذج الذكاء الاصطناعي تشيل أغلب إشارة الاختبار الصناعية (نغمة + ضوضاء)، فالتطبيع قد يقصّر قليلًا
            if not preset.startswith("ai_"):
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


class SpotifyAndSources(unittest.TestCase):
    def test_parse_links(self):
        self.assertEqual(spotify.parse("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=abc"),
                         ("track", "4cOdK2wGLETKBW3PvgPWqT"))
        self.assertEqual(spotify.parse("https://open.spotify.com/intl-ar/playlist/37i9dQZF1DXcBWIGoYBM5M"),
                         ("playlist", "37i9dQZF1DXcBWIGoYBM5M"))
        self.assertEqual(spotify.parse("spotify:album:1DFixLWuPkv3KT3TnV35m3"), ("album", "1DFixLWuPkv3KT3TnV35m3"))
        self.assertIsNone(spotify.parse("https://www.youtube.com/watch?v=abc"))

    def test_tracks_from_entities(self):
        track = {"name": "Never Gonna Give You Up", "artists": [{"name": "Rick Astley"}], "duration": 213573}
        t = spotify.tracks_from_entity("track", track)[0]
        self.assertEqual((t["title"], t["artist"], t["duration_ms"]), ("Never Gonna Give You Up", "Rick Astley", 213573))
        self.assertEqual(spotify.search_source(t), "ytsearch5:Rick Astley - Never Gonna Give You Up audio")
        playlist = {"name": "Mix", "trackList": [
            {"title": "A", "subtitle": "X, Y", "duration": 1000, "isPlayable": True},
            {"title": "B", "subtitle": "Z", "duration": 2000, "isPlayable": False}]}
        ts = spotify.tracks_from_entity("playlist", playlist)
        self.assertEqual([x["title"] for x in ts], ["A"])
        self.assertEqual(spotify.display_name(ts[0]), "X, Y - A")
        album = spotify.tracks_from_entity("album", {"name": "Alb", "trackList": [{"title": "S", "subtitle": "Q", "duration": 1}]})
        self.assertEqual(album[0]["album"], "Alb")

    def test_fetch_uses_embed_page(self):
        import json as _json
        page = '<html><script id="__NEXT_DATA__" type="application/json">' + _json.dumps(
            {"props": {"pageProps": {"state": {"data": {"entity": {
                "name": "My list", "trackList": [{"title": "T1", "subtitle": "Art", "duration": 5000, "isPlayable": True}]}}}}}}
        ) + "</script></html>"
        with mock.patch.object(core, "http_get", return_value=page.encode()):
            data = spotify.fetch("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual((data["name"], len(data["tracks"])), ("My list", 1))
        with mock.patch.object(core, "http_get", side_effect=OSError("offline")):
            with self.assertRaises(core.EnhanceError) as ctx:
                spotify.fetch("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT")
        self.assertEqual(ctx.exception.key, "err_spotify")

    def test_playlist_detection(self):
        self.assertTrue(server.looks_like_playlist("https://www.youtube.com/playlist?list=PL123"))
        self.assertTrue(server.looks_like_playlist("https://soundcloud.com/u/sets/mix"))
        self.assertFalse(server.looks_like_playlist("https://www.youtube.com/watch?v=abc&list=PL123"))
        self.assertFalse(server.looks_like_playlist("https://www.youtube.com/watch?v=abc"))

    def test_ranking_prefers_official_versions(self):
        cands = [
            {"id": "1", "title": "Song (Live at Wembley)", "channel": "Art", "duration": 205, "url": "u1"},
            {"id": "2", "title": "Art - Song (Official Video)", "channel": "ArtVEVO", "duration": 260, "url": "u2"},
            {"id": "3", "title": "Song", "channel": "Art - Topic", "duration": 201, "url": "u3"},
            {"id": "4", "title": "Song (Pianoforte)", "channel": "Art", "duration": 199, "url": "u4"},
            {"id": "5", "title": "Song sped up", "channel": "fan", "duration": 160, "url": "u5"},
            {"id": "6", "title": "Song", "channel": "YouTube Music", "duration": None, "url": "u6", "ytm": 1},
        ]
        ranked = [c["id"] for c in core.rank_candidates(cands, "Song", "Art", 200)]
        self.assertEqual(set(ranked[:2]), {"3", "6"})
        self.assertGreater(ranked.index("1"), 2)
        self.assertGreaterEqual(ranked.index("4"), 2)
        self.assertEqual(ranked[-1], "5")
        # العربي: أ / ا نفس الشي
        self.assertEqual(core._norm("الأماكن"), core._norm("الاماكن"))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
    def test_search_downloads_best_candidate_and_falls_back_on_wrong_length(self):
        cands = [{"id": "a", "title": "Song", "channel": "Art - Topic", "duration": 200, "url": "https://y/a"},
                 {"id": "b", "title": "Song", "channel": "Art", "duration": 201, "url": "https://y/b"}]
        with tempfile.TemporaryDirectory() as d:
            make_tone(Path(d) / "x.mp3")
            urls = []

            def fake_download(url, dest, cb, token=None, match_filter=None):
                urls.append(url)
                shutil.copy(Path(d) / "x.mp3", Path(dest) / f"x{len(urls)}.mp3")
                core.download.last = {"channel": "Art - Topic" if url.endswith("a") else "Art",
                                      "duration": "320" if url.endswith("a") else "201"}
                return Path(dest) / f"x{len(urls)}.mp3", None

            with mock.patch.object(core, "search_youtube", return_value=cands), \
                    mock.patch.object(core, "download", side_effect=fake_download):
                res = core.process_item("ytsearch10:Art - Song", {
                    "out_dir": d, "format": "flac", "name": "Art - Song", "duration_ms": 200000,
                    "meta": {"title": "Song", "artist": "Art", "album": "Alb"}})
                self.assertEqual(urls, ["https://y/a", "https://y/b"])   # المدة غلط: جرّب اللي بعده
                self.assertEqual(res["report"]["match"]["pick"], 1)
                self.assertEqual(res["report"]["match"]["channel"], "Art")
                self.assertEqual(len(res["candidates"]), 2)
                self.assertTrue(Path(res["output"]).name.startswith("Art - Song_enhanced"))
                tags = core.read_tags(res["output"])
                self.assertEqual((tags["title"], tags["artist"], tags["album"]), ("Song", "Art", "Alb"))
                with self.assertRaises(core.EnhanceError) as ctx:   # «مو هذي الأغنية» بعد آخر مرشح
                    core.process_item("ytsearch10:Art - Song", {"out_dir": d, "candidates": cands, "pick": 2})
                self.assertEqual(ctx.exception.key, "err_nomatch")

    def test_trim_silence_and_log(self):
        core.log("hello\nworld")
        self.assertTrue(list(core.LOG)[-1].endswith("world"))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class PlayerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core.save_config({**core.load_config(), "out": str(Path(_HOME) / "out4"), "notify": False})
        server.STATE.items.clear()
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.dir = Path(tempfile.mkdtemp())
        make_tone(cls.dir / "a_first.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(cls.dir / "a_first.mp3"), str(cls.dir / "b_second.wav")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(cls.dir / "a_first.mp3"), "-c:a", "wmav2",
                        str(cls.dir / "c_third.wma")], check=False)
        (cls.dir / "notes.txt").write_text("x")

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def call(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        c.request(method, path, body=data, headers=headers or {})
        r = c.getresponse()
        raw = r.read()
        c.close()
        return r.status, raw

    def test_queue_order_meta_direct_and_transcoded_playback(self):
        st, raw = self.call("POST", "/api/player/paths", {"paths": [str(self.dir)]})
        tracks = json.loads(raw)["tracks"]
        names = [t["name"] for t in tracks]
        self.assertEqual(names[:2], ["a_first", "b_second"])      # بالترتيب، وملف txt ما يدخل
        self.assertNotIn("notes", names)
        a = tracks[0]
        st, raw = self.call("GET", f"/api/player/meta?id={a['id']}")
        self.assertGreater(json.loads(raw)["duration"], 3)
        st, data = self.call("GET", f"/play/{a['id']}", headers={"Range": "bytes=0-9"})
        self.assertEqual((st, len(data)), (206, 10))
        # الصيغة اللي المتصفح ما يشغّلها: نسخة MP3 مؤقتة تقبل Range
        st, data = self.call("GET", f"/play/{tracks[1]['id']}?mode=transcode", headers={"Range": "bytes=0-2"})
        self.assertEqual((st, data), (206, b"ID3"))
        st, _ = self.call("GET", "/play/unknown")
        self.assertEqual(st, 404)
        # إضافة ملف آخر بدون مسح، ثم مسح الكل
        extra = self.dir / "a_first.mp3"
        st, raw = self.call("POST", "/api/player/paths", {"paths": [str(extra)], "append": True})
        self.assertEqual(len(json.loads(raw)["tracks"]), len(tracks))   # ما يتكرر
        st, raw = self.call("POST", "/api/player/clear", {})
        self.assertEqual(json.loads(raw)["tracks"], [])


class ErrorSummary(unittest.TestCase):
    def test_picks_real_error_lines_not_stream_info(self):
        text = ("Input #0, flac\nStream #0:0: Audio: flac\n[arnndn @ 000] Error opening model: No such file\n"
                "Error initializing filter 'arnndn' with args 'm=x'\nOutput #0, null\n"
                "Stream #0:0(eng): Audio: pcm_s16le, 192000 Hz\nMetadata:\nencoder : Lavc63")
        out = core._ffmpeg_error_summary(text)
        self.assertIn("Error opening model", out)
        self.assertNotIn("pcm_s16le", out)
        self.assertEqual(core._ffmpeg_error_summary("a\nb\nc\nd"), "b | c | d")


class V14Features(unittest.TestCase):
    def test_fontpack_roundtrip_hides_font_signature(self):
        blob = fontpack.pack({"r": (400, b"wOF2" + b"x" * 500), "b": (700, b"wOF2" + b"y" * 300)})
        self.assertNotIn(b"wOF2", blob)
        out = fontpack.unpack(blob)
        self.assertEqual(out["r"], (400, b"wOF2" + b"x" * 500))
        self.assertEqual(out["b"][0], 700)
        self.assertEqual(fontpack.unpack(b"garbage"), {})

    def test_m3u_playlist_and_auto_jobs(self):
        d = Path(tempfile.mkdtemp())
        (d / "sub").mkdir()
        (d / "a.mp3").write_bytes(b"x")
        (d / "sub" / "b.flac").write_bytes(b"x")
        (d / "list.m3u8").write_text("#EXTM3U\n#EXTINF:1,A\na.mp3\nsub/b.flac\nmissing.mp3\n", encoding="utf-8")
        self.assertEqual([p.name for p in core.collect_media([str(d / "list.m3u8")])], ["a.mp3", "b.flac"])
        self.assertTrue(2 <= core.auto_jobs() <= 8)

    def test_new_config_keys(self):
        cfg = core.sanitize_config({"start_player": True, "mini_corner": "top", "auto_player": False})
        self.assertEqual((cfg["start_player"], cfg["mini_corner"], cfg["auto_player"]), (True, "top", False))
        self.assertEqual(core.sanitize_config({"mini_corner": "left"})["mini_corner"], "bottom")

    def test_mini_geometry_stays_off_the_screen_edge(self):
        w, h, x, y = winctl.mini_geometry("bottom", screen=(1920, 1080))
        self.assertEqual((w, h), winctl.MINI)
        self.assertEqual(x, 1920 - w - winctl.MARGIN)
        self.assertGreaterEqual(1080 - (y + h), winctl.MARGIN)
        self.assertEqual(winctl.mini_geometry("top", screen=(1920, 1080))[3], winctl.MARGIN)

    def test_set_mode_without_window_is_harmless(self):
        saved = dict(winctl._state)
        try:
            winctl._state.update(win=None)
            self.assertFalse(winctl.set_mode("mini"))
        finally:
            winctl._state.update(saved)

    def test_set_mode_saves_and_restores_geometry(self):
        class FakeWin:
            width, height, x, y, on_top = 720, 900, 10, 20, False

            def resize(self, w, h):
                self.width, self.height = w, h

            def move(self, x, y):
                self.x, self.y = x, y
        saved = dict(winctl._state)
        try:
            win = FakeWin()
            winctl._state.update(win=win, kind="fake", saved=None, mode="full")
            with mock.patch.object(winctl, "screen_size", return_value=(1920, 1080)):
                self.assertTrue(winctl.set_mode("mini"))
                self.assertEqual((win.width, win.height, win.on_top), (*winctl.MINI, True))
                winctl.set_mode("mini_tall")
                self.assertEqual(win.height, winctl.MINI_TALL[1])
                winctl.set_mode("full")
            self.assertEqual((win.width, win.height, win.x, win.y, win.on_top), (720, 900, 10, 20, False))
        finally:
            winctl._state.clear()
            winctl._state.update(saved)


class UiFontServing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", path)
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, data

    def test_font_injected_with_session_token_and_pack_not_downloadable(self):
        old = server.STATE.ui_font
        server.STATE.ui_font = {"r": (400, b"wOF2-test")}
        try:
            st, html = self.get("/")
            self.assertIn(f"/uifont/{server.STATE.font_token}/r".encode(), html)
            st, data = self.get(f"/uifont/{server.STATE.font_token}/r")
            self.assertEqual((st, data), (200, b"wOF2-test"))
            self.assertEqual(self.get("/uifont/wrong-token/r")[0], 404)
            self.assertEqual(self.get("/static/_uifont.bin")[0], 404)
        finally:
            server.STATE.ui_font = old

    def test_no_font_means_no_injection(self):
        old = server.STATE.ui_font
        server.STATE.ui_font = {}
        try:
            self.assertNotIn(b"/uifont/", self.get("/")[1])
        finally:
            server.STATE.ui_font = old


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class V15Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        core.save_config({**core.load_config(), "out": str(cls.out), "notify": False, "trim_silence": True})
        server.STATE.items.clear()
        cls.httpd = server.make_server("window")
        cls.port = server.STATE.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def call(self, method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        c.request(method, path, body=json.dumps(body).encode() if isinstance(body, dict) else body)
        r = c.getresponse()
        raw = r.read()
        c.close()
        return r.status, raw

    def test_trim_silence_removes_leading_and_trailing_silence(self):
        d = Path(tempfile.mkdtemp())
        src = d / "padded.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=3",
                        "-f", "lavfi", "-i", "sine=f=440:d=4:r=48000", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=3",
                        "-filter_complex", "[1]aformat=channel_layouts=stereo[s];[0][s][2]concat=n=3:v=0:a=1", str(src)], check=True)
        trimmed = core.process_item(str(src), {"out_dir": str(d / "o"), "trim_silence": True})
        kept = core.process_item(str(src), {"out_dir": str(d / "o2"), "trim_silence": False})
        self.assertLess(core.media_duration(trimmed["output"]), 5.5)
        self.assertGreater(core.media_duration(kept["output"]), 9.5)

    def test_player_queue_survives_restart(self):
        f = self.out / "keep_me.mp3"
        make_tone(f)
        self.call("POST", "/api/player/paths", {"paths": [str(f)]})
        self.call("POST", "/api/player/save", {"idx": 0, "pos": 2.5})
        server.STATE.queue.clear()
        server.STATE.tracks.clear()
        server.player_restore()
        st, raw = self.call("GET", "/api/player/tracks")
        data = json.loads(raw)
        self.assertEqual([t["name"] for t in data["tracks"]], ["keep_me"])
        self.assertEqual(data["resume"], {"idx": 0, "pos": 2.5})

    def test_library_scan_play_and_delete(self):
        for n in ("lib_a", "lib_b"):
            make_tone(self.out / f"{n}_enhanced.mp3")
        make_tone(self.out / "lib_a_original.mp3")   # نسخ المقارنة ما تظهر
        for _ in range(60):
            data = json.loads(self.call("GET", "/api/library")[1])
            names = {f["name"] for f in data["files"]}
            if not data["scanning"] and {"lib_a_enhanced", "lib_b_enhanced"} <= names:
                break
            time.sleep(0.5)
        self.assertIn("lib_a_enhanced", names)
        self.assertNotIn("lib_a_original", names)
        path = str(self.out / "lib_b_enhanced.mp3")
        st, raw = self.call("POST", "/api/library/play", {"paths": [path]})
        self.assertIsNotNone(json.loads(raw)["index"])
        st, raw = self.call("POST", "/api/library/delete", {"path": path})
        self.assertTrue(json.loads(raw)["ok"])
        self.assertFalse(Path(path).exists())
        st, raw = self.call("POST", "/api/library/delete", {"path": "/etc/passwd"})   # خارج مجلد الحفظ: ممنوع
        self.assertFalse(json.loads(raw)["ok"])

    def test_lyrics_endpoint_caches(self):
        f = self.out / "Artist - Lyric Song_enhanced.mp3"
        make_tone(f)
        tid = json.loads(self.call("POST", "/api/player/paths", {"paths": [str(f)]})[1])["tracks"][0]["id"]
        lrc = "[00:01.00]first line\n[00:02.50]second line"
        with mock.patch.object(core, "fetch_lyrics", return_value={"synced": lrc, "plain": None}) as fl:
            r1 = json.loads(self.call("GET", f"/api/player/lyrics?id={tid}")[1])
            r2 = json.loads(self.call("GET", f"/api/player/lyrics?id={tid}")[1])
        self.assertEqual(r1["synced"], lrc)
        self.assertEqual(r2["synced"], lrc)
        self.assertEqual(fl.call_count, 1)                      # المرة الثانية من الكاش
        self.assertEqual(fl.call_args[0][:2], ("Lyric Song", "Artist"))

    def test_next_match_replaces_wrong_version(self):
        cands = [{"id": "a", "title": "S", "channel": "X", "duration": 4, "url": "https://y/a"},
                 {"id": "b", "title": "S", "channel": "X - Topic", "duration": 4, "url": "https://y/b"}]
        tone = Path(tempfile.mkdtemp()) / "t.mp3"
        make_tone(tone)

        def fake_download(url, dest, cb, token=None, match_filter=None):
            out = Path(dest) / f"dl_{url[-1]}.mp3"
            shutil.copy(tone, out)
            core.download.last = {"channel": "X" if url.endswith("a") else "X - Topic", "duration": "4"}
            return out, None

        with mock.patch.object(core, "search_youtube", return_value=cands), \
                mock.patch.object(core, "download", side_effect=fake_download):
            self.call("POST", "/api/submit", {"queries": ["X - S"]})
            first = None
            for _ in range(80):
                first = next((i for i in json.loads(self.call("GET", "/api/state")[1])["items"]
                              if i["label"] == "X - S" and i["status"] in ("done", "error")), None)
                if first:
                    break
                time.sleep(0.5)
            self.assertEqual(first["status"], "done", first)
            self.assertTrue(first["can_next"])
            self.assertEqual(first["result"]["match"]["pick"], 0)
            self.assertEqual(first["result"]["match"]["channel"], "X - Topic")   # الرسمية أولًا
            old_file = self.out / first["result"]["output_name"]
            self.assertEqual(self.call("POST", "/api/next_match", {"id": first["id"]})[0], 200)
            second = None
            for _ in range(80):
                items = json.loads(self.call("GET", "/api/state")[1])["items"]
                second = next((i for i in items if i["label"] == "X - S" and i["id"] != first["id"]
                               and i["status"] == "done"), None)
                if second and not any(i["id"] == first["id"] for i in items):
                    break
                time.sleep(0.5)
        self.assertEqual(second["result"]["match"]["channel"], "X")
        self.assertFalse(second["can_next"])
        self.assertFalse(old_file.exists())                    # النسخة الغلط انحذفت

    def test_log_endpoint(self):
        core.log("something happened")
        st, raw = self.call("GET", "/api/log")
        text = raw.decode()
        self.assertEqual(st, 200)
        self.assertIn(updater.VERSION, text)
        self.assertIn("something happened", text)


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
        text = updater._win_script(321, r"C:\new\App", r"C:\Users\Me\It's App", "App.exe")
        for needle in ("$waitPid = 321", r"$src = 'C:\new\App'", r"$dst = 'C:\Users\Me\It''s App'", "robocopy.exe",
                       "Wait-Process", "Start-Process -FilePath"):
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


class FrozenCodecGuard(unittest.TestCase):
    def test_no_codec_that_packaged_builds_may_lack(self):
        """النسخة المجمّعة (PyInstaller) ما فيها دايمًا ترميز utf-8-sig: نكتب BOM يدويًا بدل ما نعتمد عليه."""
        root = Path(__file__).resolve().parent.parent / "msga"
        offenders = [str(p.name) for p in root.glob("*.py") if "utf-8-sig" in p.read_text(encoding="utf-8").replace(
            "# BOM يدويًا: بعض النسخ المجمّعة ما فيها ترميز utf-8-sig", "")]
        self.assertEqual(offenders, [])

    def test_m3u_with_bom(self):
        d = Path(tempfile.mkdtemp())
        (d / "a.mp3").write_bytes(b"x")
        (d / "l.m3u").write_bytes(b"\xef\xbb\xbfa.mp3\n")
        self.assertEqual([p.name for p in core.read_m3u(d / "l.m3u")], ["a.mp3"])


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
