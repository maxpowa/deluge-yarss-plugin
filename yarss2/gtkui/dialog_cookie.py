# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import gtk
import gtk.glade
import deluge.component as component

from yarss2.util.common import get_resource


class DialogCookie():

    def __init__(self, gtkui, cookie_data):
        self.gtkUI = gtkui
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
        self.dialog.set_title("Edit Cookies" if "key" in self.cookie_data else "Add Cookies")
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
            self.gtkUI.save_cookie(self.cookie_data)
            self.dialog.destroy()

    def on_button_remove_cookie_data_clicked(self, button):
        tree_sel = self.treeview.get_selection()
        (tm, ti) = tree_sel.get_selected()
        if not ti:
            return
        v0 = tm.get_value(ti, 0)
        del self.cookie_data["value"][v0]
        self.update_cookie_values_list()

    def on_button_add_cookie_data_clicked(self, button):
        key = self.glade.get_widget("text_key").get_text().strip()
        value = self.glade.get_widget("text_value").get_text().strip()

        if len(key) > 0 and len(value):
            if key in self.cookie_data["value"]:
                return
            self.cookie_data["value"][key] = value
            self.update_cookie_values_list()
            self.glade.get_widget("text_key").set_text("")
            self.glade.get_widget("text_value").set_text("")

    def setup_cookie_list(self):
        # name and key
        self.list_store = gtk.ListStore(str, str)
        treeview = gtk.TreeView(self.list_store)

        renderertext = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Key/Name", renderertext, text=0)
        treeview.append_column(column)

        renderertext = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Value", renderertext, text=1)
        treeview.append_column(column)
        return treeview

    def on_button_cancel_clicked(self, event=None):
        self.dialog.destroy()
