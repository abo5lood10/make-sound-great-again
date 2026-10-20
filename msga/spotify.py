"""قراءة أغاني سبوتيفاي العامة (أغنية / ألبوم / قائمة) بدون مفاتيح، من صفحة الـ embed الرسمية.

ملاحظة مهمة: صوت سبوتيفاي نفسه محمي ولا يُنزَّل. نقرأ فقط أسماء الأغاني والفنانين، ثم يبحث البرنامج عن كل أغنية
في يوتيوب وينزّلها من هناك (بنفس مدة الأغنية تقريبًا). الصفحة العامة تعرض عادةً أول ~50-100 أغنية من القائمة الطويلة.
"""
import json
import re

from . import core

LINK_RE = re.compile(r"(?:open\.spotify\.com/(?:intl-[a-z]+/)?|spotify:)(track|album|playlist)[/:]([A-Za-z0-9]{22})")
DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def parse(url):
    """يرجع (النوع، المعرّف) أو None لو الرابط مو سبوتيفاي."""
    m = LINK_RE.search(str(url))
    return (m.group(1), m.group(2)) if m else None


def is_spotify(url):
    return parse(url) is not None


def _entity(kind, sid):
    try:
        html = core.http_get(f"https://open.spotify.com/embed/{kind}/{sid}").decode("utf-8", "replace")
        data = json.loads(DATA_RE.search(html).group(1))
        return data["props"]["pageProps"]["state"]["data"]["entity"]
    except Exception:
        raise core.EnhanceError("err_spotify")


def tracks_from_entity(kind, ent):
    """يحوّل بيانات الصفحة إلى قائمة {title, artist, album, duration_ms}."""
    if kind == "track":
        artists = ", ".join(a.get("name", "") for a in ent.get("artists", []) if a.get("name"))
        return [{"title": ent.get("name") or ent.get("title") or "", "artist": artists, "album": "",
                 "duration_ms": ent.get("duration") or 0}]
    album = ent.get("name", "") if kind == "album" else ""
    out = []
    for t in ent.get("trackList", []) or []:
        title = t.get("title") or ""
        if title and t.get("isPlayable", True):
            out.append({"title": title, "artist": t.get("subtitle", ""), "album": album,
                        "duration_ms": t.get("duration") or 0})
    return out


def fetch(url):
    """يرجع {kind, name, tracks}. يرمي EnhanceError('err_spotify') لو ما قدر."""
    parsed = parse(url)
    if not parsed:
        raise core.EnhanceError("err_spotify")
    kind, sid = parsed
    ent = _entity(kind, sid)
    tracks = tracks_from_entity(kind, ent)
    if not tracks:
        raise core.EnhanceError("err_spotify")
    return {"kind": kind, "name": ent.get("name") or ent.get("title") or "", "tracks": tracks}


def search_source(track):
    """نص البحث في يوتيوب (أول 5 نتائج، والفلتر على المدة يختار المناسب)."""
    q = f"{track['artist']} - {track['title']}".strip(" -")
    return f"ytsearch5:{q} audio"


def display_name(track):
    return f"{track['artist']} - {track['title']}".strip(" -") if track["artist"] else track["title"]
