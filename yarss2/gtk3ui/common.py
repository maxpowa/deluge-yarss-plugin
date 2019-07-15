import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango, GObject, PangoCairo  # noqa: F401


def popup_gtk_menu(menu_widget, treeview, event, expected_button=3):
    if event.button != expected_button:
        return False
    x = int(event.x)
    y = int(event.y)
    pthinfo = treeview.get_path_at_pos(x, y)
    if pthinfo is not None:
        path, col, cellx, celly = pthinfo
        treeview.grab_focus()
        treeview.set_cursor(path, col, 0)
        menu_widget.popup(None, None, None, None, event.button, event.time)
        menu_widget.show_all()
    return True
