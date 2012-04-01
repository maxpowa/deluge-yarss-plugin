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
import gtk.glade

from deluge.log import LOG as log
import deluge.component as component
from twisted.internet import threads

from yarss2.common import get_resource, get_value_in_selected_row, string_to_unicode
from yarss2.http import HTMLStripper
from yarss2 import rssfeed_handling

from CellrendererPango import CustomAttribute, CellrendererPango

class DialogSubscription():

    def __init__(self, gtkUI, subscription_data, rssfeeds, move_completed_list, email_messages, cookies):
        self.gtkUI = gtkUI
        self.rssfeeds = rssfeeds
        self.move_completed_list = move_completed_list
        self.email_messages = email_messages
        self.rssfeeds_dict = {}
        self.matching_store = None
        self.icon_matching = gtk.gdk.pixbuf_new_from_file(get_resource("match.png"))
        self.icon_nonmatching = gtk.gdk.pixbuf_new_from_file(get_resource("no_match.png"))
        self.subscription_data = subscription_data
        self.cookies = cookies

    def setup(self):
        self.glade = gtk.glade.XML(get_resource("dialog_subscription.glade"))
        self.glade.signal_autoconnect({
                "on_txt_regex_include_activate":       self.on_txt_regex_activate,
                "on_txt_regex_exclude_activate":       self.on_txt_regex_activate,
                "on_button_cancel_clicked":            self.on_button_cancel_clicked,
                "on_button_save_clicked":              self.on_button_save_subscription_clicked,
                "on_button_add_notication_clicked":    self.on_button_add_notication_clicked,
                "on_button_remove_notication_clicked": self.on_button_remove_notication_clicked,
                "on_rssfeed_selected":                 self.on_rssfeed_selected,
                "on_panel_matching_move_handle":       self.on_panel_matching_move_handle
                })
        # This is to make testing of the GUI possible (tests/)
        self.method_perform_rssfeed_selection = self.perform_rssfeed_selection
        
        self.dialog = self.glade.get_widget("window_subscription")
        self.setup_rssfeed_combobox()
        self.setup_move_completed_combobox()
        self.setup_messages_combobox()
        self.setup_messages_list()
        self.treeview = self.create_matching_tree()
        self.load_subscription_data()

    def show(self):
        self.setup()
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.show()

########################################
## GUI creation
########################################

    def setup_move_completed_combobox(self):
        # Create liststore model to replace default model
        self.move_completed_store = gtk.ListStore(str)
        combobox_move_completed = self.glade.get_widget("combobox_move_completed")
        combobox_move_completed.set_model(self.move_completed_store)

    def setup_rssfeed_combobox(self):
        rssfeeds_combobox = self.glade.get_widget("combobox_rssfeeds")
        rendererText = gtk.CellRendererText()
        rssfeeds_combobox.pack_start(rendererText, False)
        rssfeeds_combobox.add_attribute(rendererText, "text", 1)

        # key, name
        self.rssfeeds_store = gtk.ListStore(str, str)
        rssfeeds_combobox.set_model(self.rssfeeds_store)

    def setup_messages_combobox(self):
        messages_combobox = self.glade.get_widget("combobox_messages")
        rendererText = gtk.CellRendererText()
        messages_combobox.pack_start(rendererText, False)
        messages_combobox.add_attribute(rendererText, "text", 1)

        # key, name
        self.messages_combo_store = gtk.ListStore(str, str)
        messages_combobox.set_model(self.messages_combo_store)

    def create_matching_tree(self):
        # Matches, Title, Updated, torrent link, CustomAttribute for PangoCellrenderer
        self.matching_store = gtk.ListStore(bool, str, str, str, CustomAttribute)

        self.matching_treeView = gtk.TreeView(self.matching_store)
        #self.matching_treeView.connect("cursor-changed", self.on_subscription_listitem_activated)
        #self.matching_treeView.connect("row-activated", self.on_button_edit_subscription_clicked)
        self.matching_treeView.set_rules_hint(True)
        self.matching_treeView.connect('button-press-event', self.on_matches_list_button_press_event)

        def cell_data_func(tree_column, cell, model, tree_iter):
            if model.get_value(tree_iter, 0) == True:
                pixbuf = self.icon_matching
            else:
                pixbuf = self.icon_nonmatching
            cell.set_property("pixbuf", pixbuf)

        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Matches", renderer)
        column.set_cell_data_func(renderer, cell_data_func)
        column.set_sort_column_id(0)
        self.matching_treeView.append_column(column)

        cellrenderer = CellrendererPango()
        column = gtk.TreeViewColumn("Title", cellrenderer, text=1)
        column.add_attribute(cellrenderer, "custom", 4)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_expand(True)
        self.matching_treeView.append_column(column)

        cellrenderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Updated", cellrenderer, text=2)
        column.set_sort_column_id(2)
        self.matching_treeView.append_column(column)

        col = gtk.TreeViewColumn()
        col.set_visible(False)
        self.matching_treeView.append_column(col)

        self.list_popup_menu = gtk.Menu()
        menuitem = gtk.MenuItem("Add this torrent now")
        self.list_popup_menu.append(menuitem)
        menuitem.connect("activate", self.on_button_add_torrent_clicked)

        return self.matching_treeView

    def on_matches_list_button_press_event(self, treeview, event):
        """Shows popup on selected row when right clicking"""
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            it = self.matching_store.get_iter(pthinfo[0])
            link = self.matching_store.get_value(it, 3)
            if link is None:
                return False

            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.list_popup_menu.popup(None, None, None, event.button, time, data=path)
                self.list_popup_menu.show_all()
            return True

    def on_button_add_torrent_clicked(self, menuitem):
        torrent_link = get_value_in_selected_row(self.matching_treeView, self.matching_store, column_index=3)
        if torrent_link is not None:
            self.gtkUI.add_torrent(torrent_link)

    def setup_messages_list(self):
        # message_key, message_title, active, torrent_added, torrent_completed,
        self.messages_list_store = gtk.ListStore(str, str, bool, bool, bool)
        self.messages_treeview = gtk.TreeView(self.messages_list_store)
        self.messages_treeview.connect("row-activated", self.on_notification_list_clicked)
        self.columns_dict = {}

        def cell_data_func(tree_column, cell, model, tree_iter):
            if model.get_value(tree_iter, 2) == True:
                pixbuf = self.icon_matching
            else:
                pixbuf = self.icon_nonmatching
            cell.set_property("pixbuf", pixbuf)

        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Message Active", renderer)
        column.set_cell_data_func(renderer, cell_data_func)
        self.messages_treeview.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Message Title", rendererText, text=1)
        self.messages_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.connect("toggled", self.message_checkbox_toggled_cb, self.messages_list_store)
        column = gtk.TreeViewColumn("On torrent added", renderer, active=3)
        self.columns_dict["3"] = column
        self.messages_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.connect("toggled", self.message_checkbox_toggled_cb, self.messages_list_store)
        column = gtk.TreeViewColumn("On torrent completed", renderer, active=4)
        self.columns_dict["4"] = column
        #self.messages_treeview.append_column(column)

        viewport = self.glade.get_widget("viewport_email_notifications")
        viewport.add(self.messages_treeview)
        viewport.show_all()

    def on_panel_matching_move_handle(self, paned, scrolltype):
        
        textview = self.glade.get_widget("textview_custom_text")
        hpaned = self.glade.get_widget("hpaned_matching")

        #pos = hpaned.compute_position(400, -1, 100)
        #print "Computed pos:", pos

        #width = textview.get_style().get_font().width("w")
        #print "width:", width
        
        #print "position:", paned.get_position()
        #print "Scrolltype:", scrolltype

########################################
## GUI Update / Callbacks
########################################

    def get_selected_combobox_key(self, combobox):
        """Get the key of the currently selected item in the combobox"""
        # Get selected item
        active = combobox.get_active()
        model = combobox.get_model()
        iterator = combobox.get_active_iter()
        if iterator is None or model.get_value(iterator, 0) == -1:
            return None
        return model.get_value(iterator, 0)


### RSS Matching
###################

## Callbacks
    
    def on_rssfeed_selected(self, combobox):
        """Callback from glade when rss combobox is selected.
        Gets the results for the RSS Feed
        Runs the code that handles the parsing in a thread with Twisted, 
        to avoid the dialog waiting on startup.
        """
        self.method_perform_rssfeed_selection()

    def perform_rssfeed_selection(self):
        rssfeed_key = self.get_selected_combobox_key(self.glade.get_widget("combobox_rssfeeds"))
        d = threads.deferToThread(self.get_and_update_rssfeed_results, rssfeed_key)
        d.addCallback(self.update_matching_view_with_rssfeed_results)
        return d

    def on_txt_regex_activate(self, text_field):
        """ Callback for when Enter is pressed in either of the regex fields """
        self.perform_search()

    def get_custom_text_lines(self):
        textbuffer = self.glade.get_widget("textview_custom_text").get_buffer()
        lines = []
        text = textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter())
        text = string_to_unicode(text)
        for line in text.splitlines():
            lines.append(line.strip())
        return lines

    def get_search_settings(self):
        regex_include = self.glade.get_widget("txt_regex_include").get_text()
        regex_exclude = self.glade.get_widget("txt_regex_exclude").get_text()
        regex_include_case = self.glade.get_widget("regex_include_case").get_active()
        regex_exclude_case = self.glade.get_widget("regex_exclude_case").get_active()
        match_option_dict = {}
        match_option_dict["regex_include"] = regex_include if (len(regex_include) > 0) else None
        match_option_dict["regex_exclude"] = regex_exclude if (len(regex_exclude) > 0) else None
        match_option_dict["regex_include_ignorecase"] = not regex_include_case
        match_option_dict["regex_exclude_ignorecase"] = not regex_exclude_case

        custom_lines = self.get_custom_text_lines()
        match_option_dict["custom_text_lines"] = custom_lines
        return match_option_dict

    def perform_search(self):
        match_option_dict = self.get_search_settings()
        self.perform_matching_and_update_liststore(match_option_dict)
        # Insert treeview
        self.set_matching_window_child(self.treeview)

## Perform matching and update liststore (which updates GUI)

    def perform_matching_and_update_liststore(self, match_option_dict):
        """Updates the rssfeed_dict with matching according to
        options in match_option_dict
        Also updates the GUI
        """
        if not self.rssfeeds_dict and not match_option_dict["custom_text_lines"]:
            return
        try:
            matchins, message = rssfeed_handling.update_rssfeeds_dict_matching(self.rssfeeds_dict,
                                                           options=match_option_dict)
            self.update_matching_feeds_store(self.treeview, self.matching_store,
                                             self.rssfeeds_dict, regex_matching=True)
            label_status = self.glade.get_widget("label_status")
            if message is None:
                label_status.set_text("")
            else:
                label_status.set_text(message)
        except Exception as (v):
            import traceback
            exc_str = traceback.format_exc(v)
            log.warn("YARSS: Error when matching:" + exc_str)

    def update_matching_feeds_store(self, treeview, store, rssfeeds_dict, regex_matching=False):
        """Updates the liststore of matching torrents.
        This updates the GUI"""
        store.clear()
        for key in rssfeeds_dict.keys():
            customAttributes = CustomAttribute()
            if regex_matching:
                attr = {}
                if rssfeeds_dict[key].has_key("regex_include_match"):
                    attr["regex_include_match"] = rssfeeds_dict[key]["regex_include_match"]
                if rssfeeds_dict[key].has_key("regex_exclude_match"):
                    attr["regex_exclude_match"] = rssfeeds_dict[key]["regex_exclude_match"]
                customAttributes = CustomAttribute(attributes_dict=attr)
            store.append([rssfeeds_dict[key]['matches'], rssfeeds_dict[key]['title'], 
                          rssfeeds_dict[key]['updated'], rssfeeds_dict[key]['link'], customAttributes])

    def get_and_update_rssfeed_results(self, rssfeed_key):
        rssfeeds_parsed = rssfeed_handling.get_rssfeed_parsed(self.rssfeeds[rssfeed_key], 
                                                              cookies=self.cookies)
        return rssfeeds_parsed

    def update_matching_view_with_rssfeed_results(self, rssfeeds_parsed):
        """Callback function, called when 'get_and_update_rssfeed_results'
        has finished.
        Replaces the content of the matching window.
        If valid items were retrieved, update the matching according
        to current settings.
        If no valid items, show the result as text instead.
        """
        # Bozo Exception, still elements might have been successfully parsed
        if rssfeeds_parsed.has_key("bozo_exception"):
            exception = rssfeeds_parsed["bozo_exception"]
            label_status = self.glade.get_widget("label_status")
            label_status.set_text(str(exception))

        # Failed to retrive items. Show content as text
        if not rssfeeds_parsed.has_key("items"):
            self.show_result_as_text(rssfeeds_parsed["raw_result"])
            return

        self.rssfeeds_dict = rssfeeds_parsed["items"]
                
        # Update the matching according to the current settings
        self.perform_search()

    def show_result_as_text(self, rssfeeds_parsed):
        """When failing to parse the RSS Feed, this will show the result
        in a text window with HTML tags stripped away.
        """
        result = self.get_viewable_result(rssfeeds_parsed)
        textview = gtk.TextView()
        textbuffer = textview.get_buffer()
        textview.show()
        textbuffer.set_text(result)
        # Insert widget
        self.set_matching_window_child(textview)

    def get_viewable_result(self, rssfeed_parsed):
        if not rssfeed_parsed["feed"].has_key("summary"):
            return ""
        cleaned = rssfeed_parsed["feed"]["summary"]
        s = HTMLStripper()
        s.feed(cleaned)
        return s.get_data()

    def set_matching_window_child(self, widget):
        """Insert the widget into the matching window"""
        matching_window = self.glade.get_widget("matching_window_upper")
        if matching_window.get_child():
            matching_window.remove(matching_window.get_child())
        matching_window.add(widget)

        # Quick hack to make sure the list of torrents are visible to the user.
        hpaned = self.glade.get_widget("hpaned_matching")
        if hpaned.get_position() == 0:
            max_pos = hpaned.get_property("max-position")
            hpaned.set_position(int(max_pos * 0.75))
        matching_window.show_all()


### Notifications
###################

    def on_notification_list_clicked(self, Event=None, a=None, col=None):
        """Callback for when the checkboxes (or actually just the row) 
        in notification list is clicked"""
        tree, row_iter = self.messages_treeview.get_selection().get_selected()
        if not row_iter or not col:
            return
        for column in self.columns_dict.keys():
            if self.columns_dict[column] == col:
                column = int(column)
                val = self.messages_list_store.get_value(row_iter, column)
                self.messages_list_store.set_value(row_iter, column, not val)
                return

    def on_button_add_notication_clicked(self, button):
        combobox = self.glade.get_widget("combobox_messages")
        key = self.get_selected_combobox_key(combobox)
        if key is None:
            return
        # Current notications
        message_dict = self.get_current_notifications()
        for c_key in message_dict.keys():
            # This message is already in the notifications list
            if c_key == key:
                return
        self.messages_list_store.append([key, self.email_messages[key]["name"],
                                         self.email_messages[key]["active"], False, False])

    def get_current_notifications(self):
        """ Retrieves the notifications from the notifications list"""
        notifications = {}
        row_iter = self.messages_list_store.get_iter_first()
        while row_iter is not None:
            key = self.messages_list_store.get_value(row_iter, 0)
            active = self.messages_list_store.get_value(row_iter, 2)
            on_added = self.messages_list_store.get_value(row_iter, 3)
            on_completed = self.messages_list_store.get_value(row_iter, 4)
            notifications[key] = {"on_torrent_added": on_added,
                                  "on_torrent_completed": on_completed}
            # Next row
            row_iter = self.messages_list_store.iter_next(row_iter)
        return notifications

    def message_checkbox_toggled_cb(self, cell, path, model):
        """Called when the checkboxes in the notications list are clicked"""
        for column in self.columns_dict.keys():
            if self.columns_dict[column] == cell:
                column = int(column)
                row_iter = self.messages_list_store.get_iter(path)
                reversed_value = not self.messages_list_store.get_value(row_iter, column)
                self.messages_list_store.set_value(row_iter, column, reversed_value)

    def on_button_remove_notication_clicked(self, button):
        """Callback for when remove button for notifications is clicked"""
        tree, row_iter = self.messages_treeview.get_selection().get_selected()
        if row_iter:
            self.messages_list_store.remove(row_iter)

 
## Save / Close
###################

    def on_button_save_subscription_clicked(self, Event=None, a=None, col=None):
        if self.save_subsription_data():
            self.dialog.destroy()

    def save_subsription_data(self):
        name = self.glade.get_widget("txt_name").get_text()
        regex_include = self.glade.get_widget("txt_regex_include").get_text()
        regex_exclude = self.glade.get_widget("txt_regex_exclude").get_text()
        regex_include_case_sensitive = self.glade.get_widget("regex_include_case").get_active()
        regex_exclude_case_sensitive = self.glade.get_widget("regex_exclude_case").get_active()
        move_completed = self.glade.get_widget("combobox_move_completed").get_active_text()
        add_torrents_paused = self.glade.get_widget("checkbox_add_torrents_in_paused_state").get_active()


        textbuffer = self.glade.get_widget("textview_custom_text").get_buffer()
        custom_text_lines = textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter())   
        
        rss_key = self.get_selected_combobox_key(self.glade.get_widget("combobox_rssfeeds"))

        # RSS feed is mandatory
        if not rss_key:
            self.rssfeed_is_mandatory_message()
            return False

        self.subscription_data["name"] = name
        self.subscription_data["regex_include"] = regex_include
        self.subscription_data["regex_exclude"] = regex_exclude
        self.subscription_data["regex_include_ignorecase"] = not regex_include_case_sensitive
        self.subscription_data["regex_exclude_ignorecase"] = not regex_exclude_case_sensitive
        self.subscription_data["move_completed"] = move_completed
        self.subscription_data["custom_text_lines"] = custom_text_lines
        self.subscription_data["rssfeed_key"] = rss_key
        self.subscription_data["add_torrents_in_paused_state"] = add_torrents_paused
        # Get notifications from notifications list
        self.subscription_data["email_notifications"] = self.get_current_notifications()
        # Call save method in gtui. Saves to core
        self.gtkUI.save_subscription(self.subscription_data)
        return True

    def rssfeed_is_mandatory_message(self):
        md = gtk.MessageDialog(self.dialog, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_CLOSE, "You must select a RSS Feed")
        md.run()
        md.destroy()

    def on_button_cancel_clicked(self, Event=None):
        self.dialog.destroy()


########################################
## Load data on creation
########################################


    def load_subscription_data(self):
        self.load_basic_fields_data()
        self.load_rssfeed_combobox_data()
        self.load_notifications_list_data()
        self.load_move_completed_combobox_data()

    def load_basic_fields_data(self):
        if self.subscription_data is None:
            return
        self.glade.get_widget("txt_name").set_text(self.subscription_data["name"])
        self.glade.get_widget("txt_regex_include").set_text(self.subscription_data["regex_include"])
        self.glade.get_widget("txt_regex_exclude").set_text(self.subscription_data["regex_exclude"])
        self.glade.get_widget("regex_include_case").set_active(
            not self.subscription_data["regex_include_ignorecase"])
        self.glade.get_widget("regex_exclude_case").set_active(
            not self.subscription_data["regex_exclude_ignorecase"])

        # Add torrents paused
        self.glade.get_widget("checkbox_add_torrents_in_paused_state").set_active(
            self.subscription_data["add_torrents_in_paused_state"])

        textbuffer = self.glade.get_widget("textview_custom_text").get_buffer()
        textbuffer.set_text(self.subscription_data["custom_text_lines"])

    def load_rssfeed_combobox_data(self):
        rssfeed_key = "-1"
        active_index = -1

        if self.subscription_data:
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

        # Set active index
        self.glade.get_widget("combobox_rssfeeds").set_active(active_index)
        # Update matching
        self.on_txt_regex_activate(None)

    def load_notifications_list_data(self):
        # Load notification messages into combo
        for key in self.email_messages.keys():
            self.messages_combo_store.append([key, self.email_messages[key]["name"]])

        # Load notifications into notifications list
        # The dict keys in email_notifications are the email messages dict keys.
        for key in self.subscription_data["email_notifications"].keys():
            on_added = self.subscription_data["email_notifications"][key]["on_torrent_added"]
            on_completed = self.subscription_data["email_notifications"][key]["on_torrent_completed"]
            self.messages_list_store.append([key, self.email_messages[key]["name"],
                                             self.email_messages[key]["active"],
                                             on_added, on_completed])

    def load_move_completed_combobox_data(self):
        move_completed_value = None
        move_completed_index = -1

        # Load the move completed values
        for i in range(len(self.move_completed_list)):
            if self.move_completed_list[i] == self.subscription_data["move_completed"]:
                move_completed_index = i
            self.move_completed_store.append([self.move_completed_list[i]])

        # Set active value in combobox
        if move_completed_index != -1:
            self.glade.get_widget("combobox_move_completed").set_active(move_completed_index)
