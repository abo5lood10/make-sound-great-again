"""إضافات سطح المكتب على ويندوز: أزرار الوسائط في الكيبورد (تشتغل حتى لو البرنامج مو قدامك) + أيقونة جنب الساعة."""
import os
import threading

from . import core

WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
MEDIA_KEYS = {"toggle": 0xB3, "next": 0xB0, "prev": 0xB1, "stop": 0xB2}


def start_media_keys(callback):
    """يسجّل أزرار الوسائط كاختصارات عامة. يرجع (الخيط، قائمة الأزرار اللي انسجلت فعلًا عبر Event)."""
    if not core.IS_WIN:
        return None, []
    import ctypes
    from ctypes import wintypes
    ready, registered = threading.Event(), []

    def loop():
        user32 = ctypes.windll.user32
        names = list(MEDIA_KEYS)
        for i, name in enumerate(names, 1):
            if user32.RegisterHotKey(None, i, MOD_NOREPEAT, MEDIA_KEYS[name]):
                registered.append(name)
            else:  # برنامج ثاني (مثل سبوتيفاي) ماسك الزر
                core.log(f"media key '{name}' is used by another app")
        ready.set()
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and 1 <= msg.wParam <= len(names):
                try:
                    callback(names[msg.wParam - 1])
                except Exception as e:
                    core.log(f"media key error: {e}")

    th = threading.Thread(target=loop, daemon=True, name="media-keys")
    th.start()
    ready.wait(3)
    return th, registered


def start_tray(on_action, title="Make Sound Great Again"):
    """أيقونة جنب الساعة (pystray). on_action(name): show / toggle / next / prev / quit. يرجع الأيقونة أو None."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        return None
    try:
        img = Image.open(core.ROOT / "assets" / "icon.png")
    except OSError:
        return None

    def item(text, name, default=False):
        return pystray.MenuItem(text, lambda *_: on_action(name), default=default)

    ar = core.load_config().get("lang") == "ar"
    menu = pystray.Menu(
        item("إظهار البرنامج" if ar else "Show", "show", default=True),
        item("تشغيل / إيقاف" if ar else "Play / Pause", "toggle"),
        item("التالي" if ar else "Next", "next"),
        item("السابق" if ar else "Previous", "prev"),
        pystray.Menu.SEPARATOR,
        item("إغلاق البرنامج" if ar else "Quit", "quit"),
    )
    icon = pystray.Icon("msga", img, title, menu)
    try:
        icon.run_detached()
    except Exception as e:
        core.log(f"tray icon failed: {e}")
        return None
    return icon


def attach(win):
    """يربط الإضافات بنافذة pywebview: أزرار الوسائط، الأيقونة، والإغلاق إلى الأيقونة (لو مفعّل)."""
    state = {"quitting": False}

    def js(code):
        try:
            win.evaluate_js(code)
        except Exception:
            pass

    def media(name):
        js(f"window.mediaKey && window.mediaKey('{name}')")

    def action(name):
        if name == "show":
            try:
                win.show()
                win.restore()
            except Exception:
                pass
        elif name == "quit":
            state["quitting"] = True
            try:
                if state.get("tray"):
                    state["tray"].stop()
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                os._exit(0)
        else:
            media(name)

    _, keys = start_media_keys(media)
    state["keys"] = keys
    state["tray"] = start_tray(action)

    def on_closing():
        # «تكمل الموسيقى بالخلفية»: نخفي النافذة بدل ما نقفل البرنامج (والإغلاق الفعلي من الأيقونة)
        if state["tray"] and core.load_config().get("tray_close") and not state["quitting"]:
            try:
                win.hide()
            except Exception:
                return True
            return False
        if state["tray"]:
            try:
                state["tray"].stop()
            except Exception:
                pass
        return True

    try:
        win.events.closing += on_closing
    except Exception:
        pass
    return state
