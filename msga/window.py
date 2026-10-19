"""نافذة مستقلة على Linux بـ GTK + WebKit2 مباشرة (موجودة غالبًا في النظام، بدون أي مكتبة بايثون إضافية).
على Windows وmacOS نستخدم pywebview بدالها."""
import os


def _load():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        for ver in ("4.1", "4.0"):
            try:
                gi.require_version("WebKit2", ver)
                break
            except ValueError:
                continue
        else:
            return None
        from gi.repository import Gtk, WebKit2
        return Gtk, WebKit2
    except Exception:
        return None


def available():
    return _load() is not None and bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def open_window(url, title, icon_path=None, width=720, height=900):
    """يفتح النافذة ويرجع بعد ما تنقفل."""
    mods = _load()
    if not mods:
        return False
    Gtk, WebKit2 = mods
    win = Gtk.Window(title=title)
    win.set_default_size(width, height)
    if icon_path and os.path.exists(icon_path):
        try:
            win.set_icon_from_file(icon_path)
        except Exception:
            pass
    view = WebKit2.WebView()
    settings = view.get_settings()
    settings.set_enable_developer_extras(False)
    settings.set_enable_write_console_messages_to_stdout(False)
    view.connect("create", lambda *_: None)  # ما نفتح نوافذ إضافية
    view.connect("context-menu", lambda *_: True)  # بدون قائمة الكليك اليمين (شكل تطبيق، مو متصفح)
    win.add(view)
    win.connect("destroy", Gtk.main_quit)
    view.load_uri(url)
    win.show_all()
    Gtk.main()
    return True
