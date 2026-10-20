"""يجهّز خط الواجهة المشفّر (للمطوّر فقط). الاستخدام:
  python scripts/make_fontpack.py Regular.woff2 Bold.woff2 out.bin            # يكتب الملف المشفّر
  python scripts/make_fontpack.py --secrets out.bin                           # يطبع أجزاء base64 لأسرار GitHub
لا ترفع ملفات الخط ولا out.bin للمستودع (الترخيص يمنع النشر).
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msga import fontpack  # noqa: E402

CHUNK = 45000  # حد أسرار GitHub 48KB

if sys.argv[1] == "--secrets":
    b64 = base64.b64encode(Path(sys.argv[2]).read_bytes()).decode()
    for i in range(0, len(b64), CHUNK):
        print(b64[i:i + CHUNK])
else:
    regular, bold, out = map(Path, sys.argv[1:4])
    Path(out).write_bytes(fontpack.pack({"r": (400, regular.read_bytes()), "b": (700, bold.read_bytes())}))
    print("written", out)
