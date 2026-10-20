"""خط الواجهة العربي (ثمانية) مضمّن داخل النسخة الجاهزة فقط، بشكل مشفّر (ترخيص الخط يسمح بالتضمين في منتج
مجمّع/مشفّر، ويمنع نشر ملفات الخط). الملف _uifont.bin ما يُرفع للمستودع أبدًا: يُركَّب وقت البناء من GitHub Secrets.
"""
import hashlib
import json
import struct

MAGIC = b"MSGAFP1\n"
_KEY = b"make-sound-great-again::ui-font::v1"


def _xor(data, nonce):
    out = bytearray(len(data))
    block = 0
    for i in range(0, len(data), 32):
        ks = hashlib.sha256(_KEY + nonce + struct.pack(">Q", block)).digest()
        block += 1
        chunk = data[i:i + 32]
        out[i:i + len(chunk)] = bytes(a ^ b for a, b in zip(chunk, ks))
    return bytes(out)


def pack(files):
    """files: {key: (weight, bytes)} -> bytes مشفّرة."""
    header, body, offset = {}, b"", 0
    for key, (weight, data) in files.items():
        header[key] = [offset, len(data), weight]
        body += data
        offset += len(data)
    head = json.dumps(header).encode()
    plain = struct.pack(">I", len(head)) + head + body
    nonce = hashlib.sha256(plain).digest()[:16]
    return MAGIC + nonce + _xor(plain, nonce)


def unpack(blob):
    """bytes -> {key: (weight, bytes)}. يرجع {} لو الملف غير صالح."""
    if not blob.startswith(MAGIC):
        return {}
    nonce = blob[len(MAGIC):len(MAGIC) + 16]
    plain = _xor(blob[len(MAGIC) + 16:], nonce)
    try:
        n = struct.unpack(">I", plain[:4])[0]
        header = json.loads(plain[4:4 + n])
    except (struct.error, ValueError):
        return {}
    body = plain[4 + n:]
    return {k: (w, body[o:o + ln]) for k, (o, ln, w) in header.items()}
