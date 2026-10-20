"""التحكم بنافذة البرنامج: وضع «المشغّل المصغّر» (مستطيل صغير قرب زاوية الشاشة) والرجوع للحجم الكامل.

ويندوز/ماك: نافذة pywebview. Linux: نافذة GTK (window.py). لو ما فيه نافذة (وضع المتصفح) ما يسوي شي.
"""
import threading

MINI = (460, 236)        # مستطيل: غلاف + عنوان + تحكم
MINI_TALL = (460, 600)   # مع قائمة التشغيل
MARGIN = 40              # بعيد عن حافة الشاشة (مو ملصوق بالزاوية)
TASKBAR = 56             # تقريب لارتفاع شريط المهام تحت

_lock = threading.Lock()
_state = {"win": None, "kind": None, "saved": None, "mode": "full"}


def register(win, kind):
    _state.update(win=win, kind=kind)


def available():
    return _state["win"] is not None


def screen_size():
    """حجم الشاشة الأساسية (بكسل منطقي)."""
    try:
        if _state["kind"] == "gtk":
            return _state["win"].screen_size()
        import webview
        s = webview.screens[0]
        return int(s.width), int(s.height)
    except Exception:
        return 1920, 1080


def mini_geometry(corner="bottom", tall=False, screen=None):
    w, h = MINI_TALL if tall else MINI
    sw, sh = screen or screen_size()
    x = max(0, sw - w - MARGIN)
    y = MARGIN if corner == "top" else max(0, sh - h - MARGIN - TASKBAR)
    return w, h, x, y


def set_mode(mode, corner="bottom"):
    """mode: full | mini | mini_tall. يرجع True لو غيّر النافذة فعلًا."""
    win = _state["win"]
    if win is None:
        return False
    with _lock:
        try:
            if mode == "full":
                saved = _state["saved"]
                win.on_top = False
                if saved:
                    win.resize(saved[0], saved[1])
                    win.move(saved[2], saved[3])
                _state.update(saved=None, mode="full")
                return True
            if _state["mode"] == "full":  # نحفظ الحجم والمكان عشان نرجع لهم
                _state["saved"] = (win.width, win.height, win.x, win.y)
            w, h, x, y = mini_geometry(corner, mode == "mini_tall")
            win.resize(w, h)
            win.move(x, y)
            win.on_top = True
            _state["mode"] = mode
            return True
        except Exception as e:  # نافذة ما تدعم هالأوامر: نكمل بدون تغيير حجمها
            print(f"window mode failed: {e}", flush=True)
            return False


def start_in_mini(corner="bottom"):
    """للتشغيل المباشر بوضع المشغّل: الحجم الكامل اللي نرجع له."""
    _state.update(saved=(720, 900, 120, 60), mode="mini")
