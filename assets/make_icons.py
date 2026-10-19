"""يولّد أيقونات البرنامج (png / ico / icns) من الصفر. التشغيل:  python assets/make_icons.py  (يحتاج Pillow)"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
S = 1024


def build():
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            k = (x + y) / (2 * S)
            px[x, y] = (int(124 + (236 - 124) * k), int(58 + (72 - 58) * k), int(237 + (153 - 237) * k), 255)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), 220, fill=255)
    img.putalpha(mask)
    d = ImageDraw.Draw(img)
    heights = [120, 240, 400, 560, 400, 640, 280, 480, 200, 320, 120]
    w, gap = 56, 28
    x0 = (S - (len(heights) * (w + gap) - gap)) // 2
    for i, h in enumerate(heights):
        x = x0 + i * (w + gap)
        d.rounded_rectangle((x, S // 2 - h // 2, x + w, S // 2 + h // 2), 28, fill=(255, 255, 255, 245))
    cx, cy, r = 800, 224, 92
    pts = []
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.3
        a = math.pi / 4 * k - math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(255, 224, 102, 255))
    return img


if __name__ == "__main__":
    big = build()
    big.resize((512, 512), Image.LANCZOS).save(HERE / "icon.png")
    big.save(HERE / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.save(HERE / "icon.icns")
    print("icons written to", HERE)
