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


class _GtkAdapter:
    """واجهة مثل نافذة pywebview (resize / move / on_top) عشان winctl يتعامل مع الاثنين بنفس الطريقة.
    كل استدعاء GTK لازم يصير في خيط الواجهة، فننفّذه عبر GLib.idle_add وننتظر النتيجة."""

    def __init__(self, win, GLib, Gdk):
        self.win, self.GLib, self.Gdk = win, GLib, Gdk

    def _call(self, fn, *a):
        import threading
        done, box = threading.Event(), {}

        def job():
            try:
                box["v"] = fn(*a)
            finally:
                done.set()
            return False
        self.GLib.idle_add(job)
        done.wait(3)
        return box.get("v")

    @property
    def width(self):
        return (self._call(self.win.get_size) or (720, 900))[0]

    @property
    def height(self):
        return (self._call(self.win.get_size) or (720, 900))[1]

    @property
    def x(self):
        return (self._call(self.win.get_position) or (0, 0))[0]

    @property
    def y(self):
        return (self._call(self.win.get_position) or (0, 0))[1]

    def resize(self, w, h):
        self._call(self.win.resize, w, h)

    def move(self, x, y):
        self._call(self.win.move, x, y)

    @property
    def on_top(self):
        return False

    @on_top.setter
    def on_top(self, value):
        self._call(self.win.set_keep_above, bool(value))

    def screen_size(self):
        def get():
            disp = self.Gdk.Display.get_default()
            mon = disp.get_primary_monitor() or disp.get_monitor(0)
            g = mon.get_workarea()
            return g.width, g.height + 56  # winctl يطرح ارتفاع شريط المهام
        return self._call(get) or (1920, 1080)


def open_window(url, title, icon_path=None, width=720, height=900, x=None, y=None, on_top=False):
    """يفتح النافذة ويرجع بعد ما تنقفل."""
    mods = _load()
    if not mods:
        return False
    Gtk, WebKit2 = mods
    from gi.repository import Gdk, GLib
    from . import winctl
    win = Gtk.Window(title=title)
    win.set_default_size(width, height)
    if x is not None and y is not None:
        win.move(x, y)
    if on_top:
        win.set_keep_above(True)
    winctl.register(_GtkAdapter(win, GLib, Gdk), "gtk")
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
