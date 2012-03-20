#
# gtkui.py
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

import yarss.rssfeed_handling

from dialog_subscription import DialogSubscription
from dialog_rssfeed import DialogRSSFeed
from dialog_email_message import DialogEmailMessage
from dialog_cookie import DialogCookie

from yarss.common import get_resource
from yarss.common import encode_cookie_values

from yarss import yarss_config
#import core

class GtkUI(GtkPluginBase):

    def enable(self):
        self.createUI()

    def disable(self):
        component.get("Preferences").remove_page("YARSS")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        pass

    def createUI(self):
        self.glade = gtk.glade.XML(get_resource("yarss_main.glade"))
        self.glade.signal_autoconnect({
                "on_button_add_subscription_clicked":       self.on_button_add_subscription_clicked,
                "on_button_delete_subscription_clicked":    self.on_button_delete_subscription_clicked,
                "on_button_edit_subscription_clicked" :     self.on_button_edit_subscription_clicked,
                                                            
                "on_button_add_rssfeed_clicked":            self.on_button_add_rssfeed_clicked,
                "on_button_delete_rssfeed_clicked":         self.on_button_delete_rssfeed_clicked,
                "on_button_edit_rssfeed_clicked" :          self.on_button_edit_rssfeed_clicked,
                                                            
                "on_button_add_cookie_clicked" :            self.on_button_add_cookie_clicked,
                "on_button_edit_cookie_clicked" :           self.on_button_edit_cookie_clicked,
                "on_button_delete_cookie_clicked":          self.on_button_delete_cookie_clicked,
                                                            
                "on_button_add_message_clicked" :           self.on_button_add_message_clicked,
                "on_button_edit_message_clicked" :          self.on_button_edit_message_clicked,
                "on_button_delete_message_clicked":         self.on_button_delete_message_clicked,
                
                "on_checkbox_email_authentication_toggled": self.on_checkbox_email_authentication_toggled,
                "on_checkbutton_send_email_on_torrent_events_toggled": 
                self.on_checkbutton_send_email_on_torrent_events_toggled
                })
        
        component.get("Preferences").add_page("YARSS", self.glade.get_widget("notebook_main"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.subscriptions = {}
        self.rssfeeds = {}
        
        self.selected_path_subscriptions = None
        self.selected_path_rssfeeds = None
        self.selected_path_email_message = None
        self.selected_path_cookies = None

        # key, enabled, name, site, download_location
        self.subscriptions_store = gtk.ListStore(str, bool, str, str, str, str)

        # key, active, name, site, Update interval, Last update
        self.rssfeeds_store = gtk.ListStore(str, bool, str, str, str, str, str)

        # key, active, site, value
        self.cookies_store = gtk.ListStore(str, bool, str, str)

        # key, active, name, to-address, subject, message-content
        self.email_messages_store = gtk.ListStore(str, bool, str, str, str, str)

        self.create_subscription_pane()
        self.create_rssfeeds_pane()
        self.create_cookies_pane()
        self.create_email_messages_pane()


##############################
# Save data and delete data from core
###############################

    def save_subscription(self, subscription_data, subscription_key=None, delete=False):
        """Called by the RSSFeed Dialog"""
        self.selected_path_rssfeeds = self.get_selection_path(self.rssfeeds_treeview)
        client.yarss.save_subscription(dict_key=subscription_key, subscription_data=subscription_data, 
                                       delete=delete).addCallback(self.cb_get_config)

    def save_rssfeed(self, rssfeed_data, rssfeed_key=None, delete=False):
        """Called by the RSSFeed Dialog"""
        self.selected_path_rssfeeds = self.get_selection_path(self.rssfeeds_treeview)
        client.yarss.save_rssfeed(dict_key=rssfeed_key, rssfeed_data=rssfeed_data, 
                                  delete=delete).addCallback(self.cb_get_config)

    def save_email_message(self, message_data, email_message_key=None, delete=False):
        self.selected_path_email_message = self.get_selection_path(self.email_messages_treeview)
        print "delete:", message_data
        print "delete:", email_message_key
        client.yarss.save_email_message(dict_key=email_message_key, message_data=message_data, 
                                        delete=delete).addCallback(self.cb_get_config)

    def save_cookie(self, cookie_data, cookie_key=None, delete=False):
        self.selected_path_cookies = self.get_selection_path(self.cookies_treeview)
        client.yarss.save_cookie(dict_key=cookie_key, cookie_data=cookie_data, 
                                 delete=delete).addCallback(self.cb_get_config)


##############################
# Update config and lists data
###############################
        
    def on_apply_prefs(self):
        """Called when the 'Apply' button is pressed"""
        self.save_configuration_data()

    def on_checkbutton_send_email_on_torrent_events_toggled(self, button):
        """Called when email notification button is toggled"""
        self.save_configuration_data()

    def save_configuration_data(self):
        # Save:
        # Settings -> Email Notifications -> Enable/Disable email notifcations
        # Settings -> Email configuration -> all fields
        # Settings -> Default values -> All fields
        
        send_email = self.glade.get_widget("checkbutton_send_email_on_torrent_events").get_active()
        from_addr = self.glade.get_widget("txt_email_from").get_text()
        smtp_server = self.glade.get_widget("txt_email_server").get_text()
        smtp_port = self.glade.get_widget("txt_email_port").get_text()
        smtp_username = self.glade.get_widget("txt_email_username").get_text()
        smtp_password = self.glade.get_widget("txt_email_password").get_text()
        enable_auth = self.glade.get_widget("checkbox_email_enable_authentication").get_active()
        
        email_configurations = {}
        email_configurations["send_email_on_torrent_events"] = send_email
        email_configurations["from_address"] = from_addr
        email_configurations["smtp_server"] = smtp_server
        email_configurations["smtp_port"] = smtp_port
        email_configurations["smtp_authentication"] = enable_auth
        email_configurations["smtp_username"] = smtp_username
        email_configurations["smtp_password"] = smtp_password

        conf = {"email_configurations": email_configurations}
        client.yarss.set_config(conf)

    def on_show_prefs(self):
        """Called when showing preferences window"""
        client.yarss.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """Callback function called after saving data to core"""
        if config == None:
            log.error("YARSS: An error has occured. Cannot load data from config")
        else:
            self.update_data_from_config(config)

    def update_data_from_config(self, config):
        self.subscriptions = config.get('subscriptions', {})
        self.rssfeeds = config.get('rssfeeds', {})
        self.cookies = config.get('cookies', {})
        self.email_messages = config.get('email_messages', {})
        self.email_config = config.get('email_configurations', {})
        
        # Update GUI
        self.update_subscription_list(self.subscriptions_store)
        self.update_rssfeeds_list(self.rssfeeds_store)
        self.update_cookies_list(self.cookies_store)
        self.update_email_messages_list(self.email_messages_store)

        # Set selection for each treeview
        if self.selected_path_subscriptions:
            self.subscriptions_treeview.get_selection().select_path(self.selected_path_subscriptions) 

        if self.selected_path_rssfeeds:
            self.rssfeeds_treeview.get_selection().select_path(self.selected_path_rssfeeds) 
        
        if self.selected_path_email_message:
            self.email_messages_treeview.get_selection().select_path(self.selected_path_email_message) 

        if self.selected_path_cookies:
            self.cookies_treeview.get_selection().select_path(self.selected_path_cookies) 

        # Email configurations
        send_email = self.glade.get_widget("checkbutton_send_email_on_torrent_events")
        from_addr = self.glade.get_widget("txt_email_from")
        smtp_server = self.glade.get_widget("txt_email_server")
        smtp_port = self.glade.get_widget("txt_email_port")
        smtp_username = self.glade.get_widget("txt_email_username")
        smtp_password = self.glade.get_widget("txt_email_password")
        enable_auth = self.glade.get_widget("checkbox_email_enable_authentication")
        
        send_email.set_active(self.email_config["send_email_on_torrent_events"])
        from_addr.set_text(self.email_config["from_address"])
        smtp_server.set_text(self.email_config["smtp_server"])
        smtp_port.set_text(self.email_config["smtp_port"])

        enable_auth.set_active(self.email_config["smtp_authentication"])
        smtp_username.set_text(self.email_config["smtp_username"])
        smtp_password.set_text(self.email_config["smtp_password"])

    def update_subscription_list(self, subscriptions_store):
        subscriptions_store.clear()
        for key in self.subscriptions.keys():
            rssfeed_key = self.subscriptions[key]["rssfeed_key"]
            subscriptions_store.append([self.subscriptions[key]["key"],
                                        self.subscriptions[key]["active"],
                                        self.subscriptions[key]["name"],
                                        self.rssfeeds[rssfeed_key]["name"],
                                        self.rssfeeds[rssfeed_key]["site"],
                                        self.subscriptions[key]["move_completed"]])

    def update_rssfeeds_list(self, rssfeeds_store):
        rssfeeds_store.clear()
        active_subscriptions = self.get_subscription_count_for_feeds()
        for key in self.rssfeeds.keys():
            active_subs = "0"
            if active_subscriptions.has_key(key):
                tmp = active_subscriptions[key]
                active_subs = "%s (%s)" % (tmp[0], tmp[1])
            rssfeeds_store.append([self.rssfeeds[key]["key"],
                                   self.rssfeeds[key]["active"],
                                   self.rssfeeds[key]["name"],
                                   self.rssfeeds[key]["site"],
                                   self.rssfeeds[key]["update_interval"],
                                   self.rssfeeds[key]["last_update"], active_subs])

    def update_cookies_list(self, cookies_store):
        cookies_store.clear()
        # key, active, site, value
        for key in self.cookies.keys():
            cookies_store.append([key, self.cookies[key]["active"],
                                  self.cookies[key]["site"],
                                  encode_cookie_values(self.cookies[key]["value"])])

    def update_email_messages_list(self, store):
        store.clear()
        # key, active, name, to-address, subject, message-content
        for key in self.email_messages.keys():
            store.append([key, self.email_messages[key]["active"],
                          self.email_messages[key]["name"],
                          self.email_messages[key]["to_address"],
                          self.email_messages[key]["subject"],
                          self.email_messages[key]["message"],
                          ])

    def get_subscription_count_for_feeds(self):
        """Creates the subscription count for each RSS Feed shown in the RSS Feeds list"""
        result = {}
        for key in self.subscriptions.keys():
            rssfeed_key = self.subscriptions[key]["rssfeed_key"]
            index = 0 if self.subscriptions[key]["active"] == True else 1
            if not result.has_key(rssfeed_key):
                result[rssfeed_key] = [0, 0]
            result[rssfeed_key][index] += 1
        return result

    def get_selection_path(self, treeview):
        """Returns the (first) selected path from a treeview"""
        tree_selection = treeview.get_selection()
        model, tree_paths = tree_selection.get_selected_rows()
        if len(tree_paths) > 0:
            return tree_paths[0]
        return None


#########################
# Create Subscription list
#########################

    def create_subscription_pane(self):
        subscriptions_box = self.glade.get_widget("subscriptions_box")
        subscriptions_window = gtk.ScrolledWindow()
        subscriptions_window.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        subscriptions_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        subscriptions_box.pack_start(subscriptions_window, True, True, 0)

        self.subscriptions_treeview = gtk.TreeView(self.subscriptions_store)
        self.subscriptions_treeview.connect("cursor-changed", self.on_subscription_listitem_activated)
        self.subscriptions_treeview.connect("row-activated", self.on_button_edit_subscription_clicked)
        self.subscriptions_treeview.set_rules_hint(True)

        self.create_subscription_columns(self.subscriptions_treeview)
        subscriptions_window.add(self.subscriptions_treeview)
        subscriptions_window.show_all()

    def create_subscription_columns(self, subscriptions_treeView):
        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Active", rendererToggle, activatable=1, active=1)
        column.set_sort_column_id(1)
        subscriptions_treeView.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text('Double-click to toggle')
        subscriptions_treeView.set_tooltip_cell(tt, None, None, rendererToggle)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", rendererText, text=2)
        column.set_sort_column_id(2)
        subscriptions_treeView.append_column(column)
        tt2 = gtk.Tooltip()
        tt2.set_text('Double-click to edit')
        #subscriptions_treeView.set_tooltip_cell(tt2, None, column, None)
        subscriptions_treeView.set_has_tooltip(True)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Feed name", rendererText, text=3)
        column.set_sort_column_id(3)
        subscriptions_treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Site", rendererText, text=4)
        column.set_sort_column_id(4)
        subscriptions_treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Move Completed", rendererText, text=5)
        column.set_sort_column_id(5)
        subscriptions_treeView.append_column(column)

#########################
# Create RSS Feeds list
#########################

    def create_rssfeeds_pane(self):
        rssfeeds_box = self.glade.get_widget("rssfeeds_box")
        
        self.rssfeeds_treeview = gtk.TreeView(self.rssfeeds_store)
        #self.subscriptions_treeview.connect("cursor-changed", self.on_listitem_activated)
        self.rssfeeds_treeview.connect("row-activated", self.on_button_edit_rssfeed_clicked)
        self.rssfeeds_treeview.set_rules_hint(True)

        self.create_feeds_columns(self.rssfeeds_treeview)
        rssfeeds_box.add(self.rssfeeds_treeview)
        rssfeeds_box.show_all()

    def create_feeds_columns(self, treeView):
        # key, active, name, site, Update interval, Last update

        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Active", rendererToggle, activatable=1, active=1)
        column.set_sort_column_id(1)
        treeView.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text('Double-click to toggle')
        treeView.set_tooltip_cell(tt, None, None, rendererToggle)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Feed Name", rendererText, text=2)
        column.set_sort_column_id(2)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Site", rendererText, text=3)
        column.set_sort_column_id(3)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Update interval", rendererText, text=4)
        column.set_sort_column_id(4)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Last update", rendererText, text=5)
        column.set_sort_column_id(5)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Subscriptions", rendererText, text=6)
        column.set_sort_column_id(6)
        treeView.append_column(column)

#########################
# Create Messages list
#########################

    def create_email_messages_pane(self):
        viewport = self.glade.get_widget("viewport_email_messages_list")
        self.email_messages_treeview = gtk.TreeView(self.email_messages_store)
        self.email_messages_treeview.connect("row-activated", self.on_button_edit_message_clicked)
        self.create_messages_columns(self.email_messages_treeview)
        viewport.add(self.email_messages_treeview)
        viewport.show_all()

    def create_messages_columns(self, treeview):
        #Store: key, active, name, to-address, subject, message-content
        
        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Active", rendererToggle, activatable=1, active=1)
        column.set_sort_column_id(1)
        treeview.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text('Double-click to toggle')
        treeview.set_tooltip_cell(tt, None, None, rendererToggle)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", rendererText, text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("To address", rendererText, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Subject", rendererText, text=4)
        column.set_sort_column_id(4)
        treeview.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Message", rendererText, text=5)
        column.set_sort_column_id(5)
        treeview.append_column(column)


#########################
# Create Cookies list
#########################

    def create_cookies_pane(self):
        viewport = self.glade.get_widget("viewport_cookies_list")
        self.cookies_treeview = gtk.TreeView(self.cookies_store)
        self.cookies_treeview.connect("row-activated", self.on_button_edit_cookie_clicked)
        self.create_cookies_columns(self.cookies_treeview)
        viewport.add(self.cookies_treeview)
        viewport.show_all()

    def create_cookies_columns(self, treeview):
        # store: key, active, site, value

        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Active", rendererToggle, activatable=1, active=1)
        column.set_sort_column_id(1)
        treeview.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text('Double-click to toggle')
        treeview.set_tooltip_cell(tt, None, None, rendererToggle)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Site", rendererText, text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        tt2 = gtk.Tooltip()
        tt2.set_text('Double-click to edit')
        #treeview.set_tooltip_cell(tt2, None, column, None)
        treeview.set_has_tooltip(True)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Value", rendererText, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)


########################################################
###  CALLBACK FUNCTIONS from Glade GUI
########################################################

#############################
# SUBSCRIPTION callbacks
#############################

    def on_button_add_subscription_clicked(self,Event=None, a=None, col=None):
        fresh_subscription_config = yarss_config.get_fresh_subscription_config()
        subscription_dialog = DialogSubscription(self, fresh_subscription_config, self.rssfeeds, self.get_move_completed_list(), self.email_messages)
        subscription_dialog.show()

    def get_move_completed_list(self):
        values = []
        for key in self.subscriptions.keys():
            value = self.subscriptions[key]["move_completed"].strip()
            if len(value) > 0:
                values.append(value)
        return values

    def on_button_delete_subscription_clicked(self,Event=None, a=None, col=None):
        tree, tree_id = self.subscriptions_treeview.get_selection().get_selected()
        key = name = str(self.subscriptions_store.get_value(tree_id, 0))
        if key:
            self.save_subscription(None, subscription_key=key, delete=True)

    def on_button_test_clicked(self, Event=None, a=None, col=None):
        client.yarss.run_feed_test()

    def on_button_edit_subscription_clicked(self, Event=None, a=None, col=None):
        tree, tree_id = self.subscriptions_treeview.get_selection().get_selected()
        key = str(self.subscriptions_store.get_value(tree_id, 0))
        if key:
            if col and col.get_title() == 'Active':
                self.subscriptions[key]["active"] = not self.subscriptions[key]["active"]
                self.save_subscriptions(self.subscriptions[key])
            else:
                edit_subscription_dialog = DialogSubscription(self, self.subscriptions[key], self.rssfeeds, self.get_move_completed_list(), self.email_messages)
                edit_subscription_dialog.show()

    def on_subscription_listitem_activated(self, treeview):
        tree, tree_id = self.subscriptions_treeview.get_selection().get_selected()
        if tree_id:
            self.glade.get_widget('button_edit_subscription').set_sensitive(True)
            self.glade.get_widget('button_delete_subscription').set_sensitive(True)
        else:
            self.glade.get_widget('button_edit_subscription').set_sensitive(False)
            self.glade.get_widget('button_delete_subscription').set_sensitive(False)

#############################
# RSS Feed callbacks
#############################

    def on_button_add_rssfeed_clicked(self,Event=None, a=None, col=None):
        # Get fresh config
        fresh_subscription_config = yarss_config.get_fresh_rssfeed_config()
        rssfeed_dialog = DialogRSSFeed(self, fresh_subscription_config)
        rssfeed_dialog.show()

    def on_button_delete_rssfeed_clicked(self,Event=None, a=None, col=None):
        tree, tree_id = self.rssfeeds_treeview.get_selection().get_selected()
        key = name = str(self.rssfeeds_store.get_value(tree_id, 0))
        if key:
            self.save_rssfeed(None, rssfeed_key=key, delete=True)
            
    def on_button_edit_rssfeed_clicked(self, Event=None, a=None, col=None):
        tree, tree_id = self.rssfeeds_treeview.get_selection().get_selected()
        key = str(self.rssfeeds_store.get_value(tree_id, 0))
        if key:
            if col and col.get_title() == 'Active':
                # Save to config
                self.rssfeeds[key]["active"] = not self.rssfeeds[key]["active"]
                self.save_rssfeed(self.rssfeeds[key])
            else:
                edit_rssfeed_dialog = DialogRSSFeed(self, self.rssfeeds[key])
                edit_rssfeed_dialog.show()

    def on_rssfeed_listitem_activated(self, treeview):
        tree, tree_id = self.rssfeeds_treeview.get_selection().get_selected()
        if tree_id:
            self.glade.get_widget('button_edit_rssfeed').set_sensitive(True)
            self.glade.get_widget('button_delete_rssfeed').set_sensitive(True)
        else:
            self.glade.get_widget('button_edit_rssfeed').set_sensitive(False)
            self.glade.get_widget('button_delete_rssfeed').set_sensitive(False)


#############################
# EMAIL MESSAGE callbacks
#############################

    def on_button_add_message_clicked(self, button):
        fresh_message_config = yarss_config.get_fresh_message_config()
        dialog = DialogEmailMessage(self, fresh_message_config)
        dialog.show()

    def on_button_edit_message_clicked(self, Event=None, a=None, col=None):
        tree, tree_id = self.email_messages_treeview.get_selection().get_selected()
        key = str(self.email_messages_store.get_value(tree_id, 0))
        if key:
            if col and col.get_title() == 'Active':
                # Save to config
                self.email_messages[key]["active"] = not self.email_messages[key]["active"]
                self.save_email_message(self.email_messages[key])
            else:
                edit_message_dialog = DialogEmailMessage(self, self.email_messages[key])
                edit_message_dialog.show()

    def on_button_delete_message_clicked(self, button):
        tree_sel = self.email_messages_treeview.get_selection()

        #TreeModel, treeIter
        (tm, ti) = tree_sel.get_selected()
        # No selection
        if not ti:
            return

        # Get the message dictionary key
        dict_key = tm.get_value(ti, 0)

        model, tree_paths = tree_sel.get_selected_rows()
        #tree_sel.select_path(tree_paths[0])

        print "tree_paths:", tree_paths
        print "tree_paths[0]:", tree_paths[0]

        self.selected_path = tree_paths[0]

        # Delete from core config
        self.save_email_message(None, email_message_key=dict_key, delete=True)



    def on_checkbox_email_authentication_toggled(self, button):
        auth_enable = self.glade.get_widget("checkbox_email_enable_authentication")
        self.glade.get_widget("txt_email_username").set_sensitive(auth_enable.get_active())
        self.glade.get_widget("txt_email_password").set_sensitive(auth_enable.get_active())


##############################
# COOKIE callbacks
##############################
    def on_button_add_cookie_clicked(self, button):
        fresh_subscription_config = yarss_config.get_fresh_cookie_config()
        dialog = DialogCookie(self, fresh_subscription_config)
        dialog.show()

    def on_button_edit_cookie_clicked(self, Event=None, a=None, col=None):
        tree, tree_id = self.cookies_treeview.get_selection().get_selected()
        key = str(self.cookies_store.get_value(tree_id, 0))
        if key:
            if col and col.get_title() == 'Active':
                # Save to config
                self.cookies[key]["active"] = not self.cookies[key]["active"]
                self.save_cookie(self.cookies[key])
            else:
                dialog_cookie = DialogCookie(self, self.cookies[key])
                dialog_cookie.show()

    def on_button_delete_cookie_clicked(self, button):
        tree_sel = self.cookies_treeview.get_selection()
        (tm, ti) = tree_sel.get_selected()
        # No selection
        if not ti:
            return
        # Get the cookie dictionary key
        cookie_key = tm.get_value(ti, 0)
        self.save_cookie(None, cookie_key=cookie_key, delete=True)
        

