#
# dialog_cookie.py
#
# Copyright (C) 2012 Bro
#
# Based on work by:
# Copyright (C) 2009 Camillo Dell'mour <cdellmour@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#       The Free Software Foundation, Inc.,
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk
from deluge.log import LOG as log
import deluge.component as component

from yarss2.common import get_resource

class DialogCookie():

    def __init__(self, gtkUI, cookie_data):
        self.gtkUI = gtkUI
        self.cookie_data = cookie_data
        self.glade = gtk.glade.XML(get_resource("dialog_cookie.glade"))
        self.glade.signal_autoconnect({
                "on_button_add_cookie_data_clicked": self.on_button_add_cookie_data_clicked,
                "on_button_remove_cookie_data_clicked": self.on_button_remove_cookie_data_clicked,
                "on_button_save_clicked": self.on_button_save_clicked,
                "on_button_cancel_clicked": self.on_button_cancel_clicked
        })
        self.treeview = self.setup_cookie_list()

        if self.cookie_data:
            self.glade.get_widget("text_site").set_text(self.cookie_data["site"])

        # Update cookie data list
        self.update_cookie_values_list()

    def show(self):
        cookie_list = self.glade.get_widget("viewport_list_cookie_values")
        cookie_list.add(self.treeview)
        cookie_list.show_all()
        self.dialog = self.glade.get_widget("dialog_cookie")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.run()

    def update_cookie_values_list(self):
        """Update list from values"""
        self.list_store.clear()
        for key in self.cookie_data["value"]:
            self.list_store.append((key, self.cookie_data["value"][key]))

    def on_button_save_clicked(self, button):
        """Saves cookie to config"""
        site = self.glade.get_widget("text_site").get_text().strip()
        if site != "":
            self.cookie_data["site"] = site
            #self.cookie_data["value"] = self.values
            self.gtkUI.save_cookie(self.cookie_data)
            self.dialog.destroy()

    def on_button_remove_cookie_data_clicked(self, button):
        tree_sel = self.treeview.get_selection()
        (tm, ti) = tree_sel.get_selected()
        if not ti:
            return
        v0 = tm.get_value(ti, 0)
        #v1 = tm.get_value(ti, 1)
        del self.cookie_data["value"][v0]
        self.update_cookie_values_list()

    def on_button_add_cookie_data_clicked(self, button):
        key = self.glade.get_widget("text_key").get_text().strip()
        value = self.glade.get_widget("text_value").get_text().strip()

        if len(key) > 0 and len(value):
            if self.cookie_data["value"].has_key(key):
                return
            self.cookie_data["value"][key] = value
            self.update_cookie_values_list()
            self.glade.get_widget("text_key").set_text("")
            self.glade.get_widget("text_value").set_text("")

    def setup_cookie_list(self):
        # name and key
        self.list_store = gtk.ListStore(str, str)
        treeView = gtk.TreeView(self.list_store)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Key/Name", rendererText, text=0)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Value", rendererText, text=1)
        treeView.append_column(column)
        return treeView

    def on_button_cancel_clicked(self, Event=None):
        self.dialog.destroy()
