"""وقت البناء (CI): يجمع أجزاء الخط من متغيرات البيئة THM_PACK_1..N (أسرار GitHub) ويكتب msga/web/_uifont.bin.
لو الأسرار غير موجودة (نسخة منسوخة من المشروع مثلًا) يكمل البناء بدون الخط."""
import base64
import os
from pathlib import Path

sys_parts = [os.environ.get(f"THM_PACK_{i}", "") for i in range(1, 13)]
b64 = "".join(p.strip() for p in sys_parts)
out = Path(__file__).resolve().parent.parent / "msga" / "web" / "_uifont.bin"
if not b64:
    print("no UI font secrets: building without the embedded Arabic font")
else:
    out.write_bytes(base64.b64decode(b64))
    print("UI font pack written:", out.stat().st_size, "bytes")
