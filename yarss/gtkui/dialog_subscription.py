#
# dialog_add_subscription.py
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
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from yarss.common import get_resource
from yarss.lib import feedparser
from yarss import rssfeed_handling

from CellrendererPango import CustomAttribute, CellrendererPango

class DialogSubscription():

    def __init__(self, gtkUI, subscription_data, rssfeeds, move_completed_list, email_messages, cookies):
        self.gtkUI = gtkUI
        self.rssfeeds = rssfeeds
        self.move_completed_list = move_completed_list
        self.email_messages = email_messages
        self.old_treeview = None
        self.icon_matching = gtk.gdk.pixbuf_new_from_file(get_resource("match.png"))
        self.icon_nonmatching = gtk.gdk.pixbuf_new_from_file(get_resource("no_match.png"))
        self.subscription_data = subscription_data
        self.cookies = cookies

    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_subscription.glade"))
        self.glade.signal_autoconnect({
                "on_txt_regex_include_activate":       self.on_txt_regex_activate,
                "on_txt_regex_exclude_activate":       self.on_txt_regex_activate,
                "on_button_cancel_clicked":            self.on_button_cancel_clicked,
                "on_button_save_clicked":              self.on_button_save_subscription_clicked,
                "on_button_add_notication_clicked":    self.on_button_add_notication_clicked,
                "on_button_remove_notication_clicked": self.on_button_remove_notication_clicked,
                "on_rssfeed_selected":                 self.on_rssfeed_selected
        })
        self.setup_rssfeed_combobox()
        self.setup_move_completed_combobox()
        self.setup_messages_combobox()
        self.setup_messages_list()

        self.load_subscription_data()
        
        self.dialog = self.glade.get_widget("dialog_add_feed")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.run()

    def load_subscription_data(self):
        
        rssfeed_key = "-1"
        active_index = -1
        move_completed_value = None
        move_completed_index = -1

        if self.subscription_data:
            self.glade.get_widget("txt_name").set_text(self.subscription_data["name"])
            self.glade.get_widget("txt_regex_include").set_text(self.subscription_data["regex_include"])
            self.glade.get_widget("txt_regex_exclude").set_text(self.subscription_data["regex_exclude"])

            self.glade.get_widget("regex_include_case").set_active(not self.subscription_data["regex_include_ignorecase"])
            self.glade.get_widget("regex_exclude_case").set_active(not self.subscription_data["regex_exclude_ignorecase"])
            #self.glade.get_widget("combobox_move_completed").set_active_text(self.subscription_data["move_completed"])
            

            # If, editing a subscription, set the rssfeed_key
            if self.subscription_data.has_key("rssfeed_key"):
                rssfeed_key = self.subscription_data["rssfeed_key"]

        # Load rssfeeds into the combobox
        count = 0
        for key in self.rssfeeds:
            self.rssfeeds_store.append([self.rssfeeds[key]["key"], self.rssfeeds[key]["name"]])
            if key == rssfeed_key:
                active_index = count
            count += 1

        rssfeeds_combobox = self.glade.get_widget("combobox_rssfeeds").set_active(active_index)

        # Load messages into combo
        for key in self.email_messages.keys():
            self.messages_combo_store.append([key, self.email_messages[key]["name"]])

        # Load notifications into notifications list  
        # The dict keys in email_notifications are the email messages dict keys.
        for key in self.subscription_data["email_notifications"].keys():
            on_added = self.subscription_data["email_notifications"][key]["on_torrent_added"]
            on_completed = self.subscription_data["email_notifications"][key]["on_torrent_completed"]
            self.messages_list_store.append([key, self.email_messages[key]["name"], on_added, 
                                             on_completed, self.email_messages[key]["active"]])

        # Load the move completed values
        self.move_completed_store.append([""])
        for i in range(len(self.move_completed_list)):
            if self.move_completed_list[i] == move_completed_value:
                move_completed_index = i
            self.move_completed_store.append([self.move_completed_list[i]])

        # Set move completed value
        if self.subscription_data:
            rssfeeds_combobox = self.glade.get_widget("combobox_move_completed").set_active(move_completed_index)


    def on_txt_regex_activate(self, text_field):
        """ Enter pressed in either of the regex fields """
        regex_include = self.glade.get_widget("txt_regex_include").get_text()
        regex_exclude = self.glade.get_widget("txt_regex_exclude").get_text()
        
        regex_include_case = self.glade.get_widget("regex_include_case").get_active()
        regex_exclude_case = self.glade.get_widget("regex_exclude_case").get_active()

        match_option_dict = {}
        match_option_dict["regex_include"] = regex_include if (len(regex_include) > 0) else None
        match_option_dict["regex_exclude"] = regex_exclude if (len(regex_exclude) > 0) else None
        match_option_dict["regex_include_ignorecase"] = not regex_include_case
        match_option_dict["regex_exclude_ignorecase"] = not regex_exclude_case
        self.perform_matching(match_option_dict)

    def setup_move_completed_combobox(self):
        combobox_move_completed = self.glade.get_widget("combobox_move_completed")
        # Create liststore model to replace default model 
        self.move_completed_store = gtk.ListStore(str)
        combobox_move_completed.set_model(self.move_completed_store)

    def setup_rssfeed_combobox(self):
        # name and key
        rssfeeds_combobox = self.glade.get_widget("combobox_rssfeeds")
        
        rendererText = gtk.CellRendererText()
        rssfeeds_combobox.pack_start(rendererText, False)
        rssfeeds_combobox.add_attribute(rendererText, "text", 1)
        
        self.rssfeeds_store = gtk.ListStore(str, str)
        rssfeeds_combobox.set_model(self.rssfeeds_store)

    def setup_messages_combobox(self):
        # name and key
        messages_combobox = self.glade.get_widget("combobox_messages")
        
        rendererText = gtk.CellRendererText()
        messages_combobox.pack_start(rendererText, False)
        messages_combobox.add_attribute(rendererText, "text", 1)
        
        # key, name
        self.messages_combo_store = gtk.ListStore(str, str)
        messages_combobox.set_model(self.messages_combo_store)
      

    def on_rssfeed_selected(self, combobox):
        """Gets the results for the RSS Feed"""
        rssfeed_key = self.get_selected_combobox_key(self.glade.get_widget("combobox_rssfeeds")) 
        self.rssfeeds_dict = rssfeed_handling.get_rssfeed_parsed_dict(self.rssfeeds[rssfeed_key], None)
        self.treeview = self.create_matching_tree()
        self.update_matching_feeds(self.treeview, self.matching_store, 
                                   self.rssfeeds_dict, regex_matching=False)
        
        matching_window = self.glade.get_widget("matching_window")
        # If old treview exists, remove it
        if self.old_treeview:
            matching_window.remove(self.old_treeview)
        matching_window.add(self.treeview)
        self.old_treeview = self.treeview
        matching_window.show_all()

    def update_matching_feeds(self, treeview, store, rssfeeds_dict, regex_matching=False):
        "callback for on show_prefs"
        store.clear()
        for key in rssfeeds_dict.keys():
            title = rssfeeds_dict[key]['title']
            updated = rssfeeds_dict[key]['updated']
            customAttributes = CustomAttribute()
            if regex_matching:
                attr = {}
                if rssfeeds_dict[key].has_key("regex_include_match"):
                    attr["regex_include_match"] = rssfeeds_dict[key]["regex_include_match"]
                if rssfeeds_dict[key].has_key("regex_exclude_match"):
                    attr["regex_exclude_match"] = rssfeeds_dict[key]["regex_exclude_match"]
                customAttributes = CustomAttribute(attributes_dict=attr)
            store.append([rssfeeds_dict[key]['matches'], title, updated, customAttributes])

    def perform_matching(self, match_option_dict):
        try:
            rssfeed_handling.update_rssfeeds_dict_matching(self.rssfeeds_dict, options=match_option_dict)
            self.update_matching_feeds(self.treeview, self.matching_store, self.rssfeeds_dict, regex_matching=True)
        except Exception as (v):
            print "Regex syntax error:", v
            # TODO: Give user the message

    def create_matching_tree(self):
        self.matching_store = gtk.ListStore(bool, str, str, CustomAttribute)
        
        self.matching_treeView = gtk.TreeView(self.matching_store)
        #self.matching_treeView.connect("cursor-changed", self.on_subscription_listitem_activated)
        #self.matching_treeView.connect("row-activated", self.on_button_edit_subscription_clicked)
        self.matching_treeView.set_rules_hint(True)

        def cell_data_func(tree_column, cell, model, tree_iter):
            if model.get_value(tree_iter, 0) == True:
                pixbuf = self.icon_matching
            else:
                pixbuf = self.icon_nonmatching

            cell.set_property("pixbuf", pixbuf)

        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Matches", renderer) #, pixbuf=COL_PIXBUF)
        column.set_cell_data_func(renderer, cell_data_func)
        column.set_sort_column_id(0)
        self.matching_treeView.append_column(column)

        cellrenderer = CellrendererPango()
        #column = gtk.TreeViewColumn("Title", cellrenderer, markup=1)
        column = gtk.TreeViewColumn("Title", cellrenderer, text=1)
        column.add_attribute(cellrenderer, "custom", 3)
        column.set_sort_column_id(1)
        column.set_resizable(True);
        self.matching_treeView.append_column(column)

        cellrenderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Updated", cellrenderer, text=2)
        column.set_sort_column_id(2)
        self.matching_treeView.append_column(column)
        
        col = gtk.TreeViewColumn()
        col.set_visible(False)
        self.matching_treeView.append_column(col)
        
        return self.matching_treeView


    def setup_messages_list(self):
        # message_key, message_title, torrent_added, torrent_completed, active
        self.messages_list_store = gtk.ListStore(str, str, bool, bool, bool)
        self.messages_treetiew = gtk.TreeView(self.messages_list_store)

        def cell_data_func(tree_column, cell, model, tree_iter):
            if model.get_value(tree_iter, 4) == True:
                pixbuf = self.icon_matching
            else:
                pixbuf = self.icon_nonmatching

            cell.set_property("pixbuf", pixbuf)

        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Active", renderer) #, pixbuf=COL_PIXBUF)
        column.set_cell_data_func(renderer, cell_data_func)
        self.messages_treetiew.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Title", rendererText, text=1)
        self.messages_treetiew.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("On torrent added", rendererText, text=2)
        self.messages_treetiew.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("On torrent completed", rendererText, text=3)
        self.messages_treetiew.append_column(column)

        viewport = self.glade.get_widget("viewport_email_notifications")
        viewport.add(self.messages_treetiew)
        viewport.show_all()

    def get_selected_combobox_key(self, combobox):
        # Get selected item
        active = combobox.get_active()
        model = combobox.get_model()
        iterator = combobox.get_active_iter()
        if iterator == None or model.get_value(iterator, 1) == -1:
            return None
        return model.get_value(iterator, 0)

    def on_button_add_notication_clicked(self, button):
        combobox = self.glade.get_widget("combobox_messages")
        key = self.get_selected_combobox_key(combobox)

        if key == None:
            return
        
        on_added = self.glade.get_widget("checkbox_on_torrent_added").get_active()
        on_completed = self.glade.get_widget("checkbox_on_torrent_completed").get_active()
        self.messages_list_store.append([key, self.email_messages[key]["name"], 
                                         on_added, on_completed, self.email_messages[key]["active"]])

    def on_button_remove_notication_clicked(self, button):
        print "remove notif"
        tree, tree_iter = self.messages_treetiew.get_selection().get_selected()
        print "tree_iter:", tree_iter
        
        # Remove by treeiter
        if tree_iter:
            self.messages_list_store.remove(tree_iter)

    def on_button_save_subscription_clicked(self, Event=None, a=None, col=None):
        name = self.glade.get_widget("txt_name").get_text()
        regex_include = self.glade.get_widget("txt_regex_include").get_text()
        regex_exclude = self.glade.get_widget("txt_regex_exclude").get_text()
        move_completed = self.glade.get_widget("combobox_move_completed").get_active_text()
        
        rss_key = self.get_selected_combobox_key(self.glade.get_widget("combobox_rssfeeds")) 
        
        # RSS feed is mandatory
        if not rss_key:
            self.rssfeed_is_mandatory_message()
            return

        self.subscription_data["name"] = name
        self.subscription_data["regex_include"] = regex_include
        self.subscription_data["regex_exclude"] = regex_exclude
        self.subscription_data["move_completed"] = move_completed
        self.subscription_data["rssfeed_key"] = rss_key

        # Get notifications from notifications list
        self.subscription_data["email_notifications"] = self.get_current_notifications()
        
        self.gtkUI.save_subscription(self.subscription_data)
        self.dialog.destroy()


    def get_current_notifications(self):
        # Retrieves the notifications from the notifications list
        notifications = {}
        item = self.messages_list_store.get_iter_first()
        
        while item != None:
            key = self.messages_list_store.get_value(item, 0)
            on_added = self.messages_list_store.get_value(item, 2)
            on_completed = self.messages_list_store.get_value(item, 3)
            notifications[key] = {"on_torrent_added": on_added, "on_torrent_completed": on_completed}
            # Next row
            item = self.messages_list_store.iter_next(item)
        return notifications

    def rssfeed_is_mandatory_message(self):
        md = gtk.MessageDialog(self.dialog, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_CLOSE, "You must select a RSS Feed")
        md.run()
        md.destroy()





    def on_button_cancel_clicked(self, Event=None):
        self.dialog.destroy()
