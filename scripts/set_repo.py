"""يثبّت اسم مستودع GitHub داخل msga/version.py (لتحديث البرنامج).
الاستخدام:  python scripts/set_repo.py اسم_المستخدم [اسم_المستودع]
"""
import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
user = sys.argv[1].lstrip("@")
repo = sys.argv[2] if len(sys.argv) > 2 else "make-sound-great-again"
f = Path(__file__).resolve().parent.parent / "msga" / "version.py"
text = f.read_text(encoding="utf-8")
new = re.sub(r'^GITHUB_REPO\s*=.*$', f'GITHUB_REPO = "{user}/{repo}"', text, flags=re.M)
f.write_text(new, encoding="utf-8")
print(f"GITHUB_REPO = {user}/{repo}")
