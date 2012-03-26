#
# dialog_email_message.py
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

from yarss.common import get_resource

class DialogEmailMessage():

    def __init__(self, gtkUI, message_data={}):
        self.gtkUI = gtkUI
        self.message_data = message_data

    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_email_message.glade"))
        self.glade.signal_autoconnect({
                "on_button_save_clicked": self.on_button_save_clicked,
                "on_button_cancel_clicked": self.on_button_cancel_clicked
        })
        # Add data
        if self.message_data is not None:
            self.set_initial_data(self.message_data)
        
        self.dialog = self.glade.get_widget("dialog_email_message")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        self.dialog.run()

    def set_initial_data(self, data):
        self.glade.get_widget("txt_message_name").set_text(data["name"])
        self.glade.get_widget("txt_to_address").set_text(data["to_address"])
        self.glade.get_widget("txt_subject").set_text(data["subject"])
        self.glade.get_widget("checkbutton_active").set_active(data["active"])
        self.glade.get_widget("txt_email_content").get_buffer().set_text(data["message"])

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

    def on_button_cancel_clicked(self, Event=None):
        self.dialog.destroy()
