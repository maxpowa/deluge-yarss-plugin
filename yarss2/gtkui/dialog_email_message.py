# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import gtk
import deluge.component as component
from yarss2.util.common import get_resource


class DialogEmailMessage():

    def __init__(self, gtkui, message_data={}):
        self.gtkUI = gtkui
        self.message_data = message_data

    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_email_message.glade"))
        self.glade.signal_autoconnect({
            "on_button_save_clicked": self.on_button_save_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked,
            "on_dialog_email_message_response": self.on_response,
        })
        # Add data
        if self.message_data is not None:
            self.set_initial_data(self.message_data)
        self.dialog = self.glade.get_widget("dialog_email_message")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.set_title("Edit Message" if "key" in self.message_data else "Add Message")
        self.dialog.run()

    def set_initial_data(self, data):
        self.glade.get_widget("txt_message_name").set_text(data["name"])
        self.glade.get_widget("txt_to_address").set_text(data["to_address"])
        self.glade.get_widget("txt_subject").set_text(data["subject"])
        self.glade.get_widget("checkbutton_active").set_active(data["active"])
        self.glade.get_widget("txt_email_content").get_buffer().set_text(data["message"])

    def on_response(self, widget, arg):
        # Escape key or close button (X in corner)
        if arg == -4:
            self.dialog.destroy()

    def on_button_save_clicked(self, button):
        """Saves message to config"""
        name = self.glade.get_widget("txt_message_name").get_text().strip()
        address = self.glade.get_widget("txt_to_address").get_text().strip()
        subject = self.glade.get_widget("txt_subject").get_text().strip()
        active = self.glade.get_widget("checkbutton_active").get_active()

        textbuffer = self.glade.get_widget("txt_email_content").get_buffer()
        message = textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter())

        if name == "" or address == "" or subject == "" or message == "":
            md = gtk.MessageDialog(self.dialog, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_CLOSE, "All fields are mandatory!")
            md.run()
            md.destroy()
            return

        self.message_data["name"] = name
        self.message_data["to_address"] = address
        self.message_data["subject"] = subject
        self.message_data["message"] = message
        self.message_data["active"] = active

        self.gtkUI.save_email_message(self.message_data)
        self.dialog.destroy()

    def on_button_cancel_clicked(self, event=None):
        self.dialog.destroy()
