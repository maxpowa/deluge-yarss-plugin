#
# gtkui.py
#
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
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

class EditDialog():
    def __init__(self, gtkUI):
        self.gtkUI = gtkUI
        
    def show(self, feed_config):
        self.glade = gtk.glade.XML(get_resource("dialog_edit.glade"))
        self.glade.signal_autoconnect({
            "on_cancel":self.on_cancel,
            "on_button_edit_clicked":self.on_button_edit_clicked
        })

        self.dialog = self.glade.get_widget("dialog_edit")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.load_config(feed_config)
        self.feed_config = feed_config
        self.dialog.run()

    def load_config(self, config):
        self.glade.get_widget("text_dist").set_text(config["site"])
        self.glade.get_widget("text_url").set_text(config["url"])
        self.glade.get_widget("text_regex").set_text(config["regex"])
        self.glade.get_widget("text_name").set_text(config["name"])
        self.glade.get_widget("text_quality").set_text(config["quality"])
        self.glade.get_widget("text_move_completed").set_text(config["move_completed"])
        self.glade.get_widget("text_time").set_text(config["date"])
        #self.glade.get_widget("checkbox_active").set_active(config["active"])
        self.glade.get_widget("checkbox_any").set_active(not config["search"])
        

    def on_button_edit_clicked(self, Event=None):
        self.feed_config["url"] = self.glade.get_widget("text_url").get_text()
        self.feed_config["regex"] = self.glade.get_widget("text_regex").get_text()
        self.feed_config["name"] = self.glade.get_widget("text_name").get_text()
        self.feed_config["quality"] = self.glade.get_widget("text_quality").get_text()
        self.feed_config["move_completed"] = self.glade.get_widget("text_move_completed").get_text()
        self.feed_config["date"] = self.glade.get_widget("text_time").get_text()
        self.feed_config["search"] = not self.glade.get_widget("checkbox_any").get_active()
        client.yarss.save_feed(self.feed_config).addCallback(self.gtkUI.cb_get_config)
        self.dialog.destroy()  

    def on_cancel(self, Event=None):
        self.dialog.destroy()

class AddFeedDialog():
    def __init__(self, gtkUI):
        self.gtkUI = gtkUI
        
    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_add_feed.glade"))
        self.glade.signal_autoconnect({
            "on_cancel":self.on_cancel,
            "on_button_add_feed_clicked": self.on_button_add_feed_clicked
        })
        self.dialog = self.glade.get_widget("dialog_add_feed")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.run()

    def on_button_add_feed_clicked(self, Event=None, a=None, col=None):
        name = self.glade.get_widget("txt_name").get_text()
        url = self.glade.get_widget("txt_feed").get_text()
        regex = self.glade.get_widget("txt_regex").get_text()
        move_completed = self.glade.get_widget("txt_move_completed").get_text()
        client.yarss.add_feed(url, regex, name, move_completed).addCallback(self.gtkUI.cb_get_config)
        self.dialog.destroy()

    def on_cancel(self, Event=None):
        self.dialog.destroy()

class SubscriptionDialog():
    def __init__(self, gtkUI):
        self.gtkUI = gtkUI
        
    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_subscription.glade"))
        self.glade.signal_autoconnect({
            "on_cancel" : self.on_cancel,
            "on_button_add_eztv_clicked" : self.on_button_add_eztv_clicked
        })
        self.dialog = self.glade.get_widget("dialog_subscription")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.glade.get_widget("combobox1").set_active(0)
        self.glade.get_widget("comboboxentry_quality").set_active(0)
        self.dialog.run()

    def on_button_add_eztv_clicked(self,Event=None, a=None, col=None):
        quality = self.glade.get_widget("comboboxentry_quality").child.get_text()
        client.yarss.add_eztv_abo(self.glade.get_widget("txt_show").get_text(), quality).addCallback(self.gtkUI.cb_get_config)
        self.dialog.destroy()
        
    def on_cancel(self, Event=None):
        self.dialog.destroy()


class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))
        self.glade.signal_autoconnect({
            "on_test_button_clicked": self.on_test_button_clicked,
            "on_button_add_eztv_clicked": self.on_button_add_eztv_clicked,
            "on_button_add_feed_clicked": self.on_button_add_feed_clicked,
            "on_button_test_clicked": self.on_button_test_clicked,
            "on_button_delete_clicked": self.on_button_delete_clicked,
            "on_button_edit_clicked" : self.on_edit_button_clicked
        })

        component.get("Preferences").add_page("Subscriptions", self.glade.get_widget("prefs_box2"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs) 

        self.abos = {}
        vbox = self.glade.get_widget("vbox_abos")
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        vbox.pack_start(sw, True, True, 0)
        
        self.store = self.create_model()

        self.treeView = gtk.TreeView(self.store)
        self.treeView.connect("cursor-changed", self.on_listitem_activated)
        self.treeView.connect("row-activated", self.on_edit_button_clicked)
        self.treeView.set_rules_hint(True)

        self.create_columns(self.treeView)
        sw.add(self.treeView)
        sw.show_all()

        self.editdialog = EditDialog(self)
        self.subscription_dialog = SubscriptionDialog(self)
        self.dialogfeed = AddFeedDialog(self)

    def disable(self):
        component.get("Preferences").remove_page("Subscriptions")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def create_model(self):
        store = gtk.ListStore(str, bool, str, str, str)
        for key in self.abos.keys():
            store.append([self.abos[key]["name"], self.abos[key]["active"], self.abos[key]["site"], self.abos[key]["move_completed"], self.abos[key]["key"]])
        return store

    def create_columns(self, treeView):
        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Active", rendererToggle, activatable=1, active=1)
        column.set_sort_column_id(0)    
        treeView.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text('Double-click to toggle')
        treeView.set_tooltip_cell(tt, None, None, rendererToggle)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", rendererText, text=0)
        column.set_sort_column_id(0)
        treeView.append_column(column)
        tt2 = gtk.Tooltip()
        tt2.set_text('Double-click to edit')
        #treeView.set_tooltip_cell(tt2, None, column, None)
        treeView.set_has_tooltip(True)

        rendererTextTorrentSite = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Site", rendererTextTorrentSite, text=2)
        column.set_sort_column_id(2)
        treeView.append_column(column)

        rendererTextMoveCompleted = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Move Completed", rendererTextMoveCompleted, text=3)
        column.set_sort_column_id(3)
        treeView.append_column(column)

    def on_test_button_clicked(self,Event=None, a=None, col=None):
        client.yarss.test()

    def on_button_add_eztv_clicked(self,Event=None, a=None, col=None):
        self.subscription_dialog.show()

    def on_button_add_feed_clicked(self,Event=None, a=None, col=None):
        self.dialogfeed.show()

    def on_button_delete_clicked(self,Event=None, a=None, col=None):
        tree, tree_id = self.treeView.get_selection().get_selected()
        key = name = str(self.store.get_value(tree_id, 4))
        if key:
            client.yarss.remove_feed(key).addCallback(self.cb_get_config)

    def on_button_test_clicked(self, Event=None, a=None, col=None):
        client.yarss.run_feed_test()

    def on_listitem_activated(self, treeview):
        tree, tree_id = self.treeView.get_selection().get_selected()
        if tree_id:
            self.glade.get_widget('button_edit').set_sensitive(True)
            self.glade.get_widget('button_delete').set_sensitive(True)
        else:
            self.glade.get_widget('button_edit').set_sensitive(False)
            self.glade.get_widget('button_delete').set_sensitive(False)

    def on_edit_button_clicked(self, Event=None, a=None, col=None):
        tree, tree_id = self.treeView.get_selection().get_selected()
        key = str(self.store.get_value(tree_id, 4))
        if key:
            if col and col.get_title() == 'Active':
                if self.abos[key]["active"]:
                    client.yarss.disable_feed(key)
                else:
                    client.yarss.enable_feed(key)
                self.store.set_value(tree_id, 1, not self.abos[key]["active"])
                self.abos[key]["active"] = not self.abos[key]["active"]
            else:
                self.editdialog.show(self.abos[key])

    def on_apply_prefs(self):
        config = {
            "updatetime":self.glade.get_widget("spinbutton_updatetime").get_value()
        }
        client.yarss.set_config(config)

    def on_show_prefs(self):
        client.yarss.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.abos = config.get('abos', {})
        self.store.clear()
        for key in self.abos.keys():
            self.store.append([self.abos[key]["name"], self.abos[key]["active"], self.abos[key]["site"], self.abos[key]["move_completed"], self.abos[key]["key"]])
        self.glade.get_widget("spinbutton_updatetime").set_value(config["updatetime"])

