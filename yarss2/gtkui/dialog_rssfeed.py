#
# dialog_rssfeed.py
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
from urlparse import urlparse

from deluge.log import LOG as log
import deluge.component as component

from yarss2.common import get_resource


class DialogRSSFeed():

    def __init__(self, gtkUI, rssfeed):
        self.gtkUI = gtkUI
        self.rssfeed = rssfeed

    def show(self):
        self.glade = gtk.glade.XML(get_resource("dialog_rssfeed.glade"))
        self.glade.signal_autoconnect({
                "on_button_cancel_clicked":self.on_button_cancel_clicked,
                "on_button_save_clicked": self.on_button_save_clicked
        })

        self.populate_data_fields()
        self.dialog = self.glade.get_widget("dialog_rssfeed")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        #self.glade.get_widget("spinbutton_updatetime").set_range(1, 30)
        self.dialog.run()

    def populate_data_fields(self):
        if self.rssfeed:
            self.glade.get_widget("txt_name").set_text(self.rssfeed["name"])
            self.glade.get_widget("txt_url").set_text(self.rssfeed["url"])
            self.glade.get_widget("spinbutton_updatetime").set_value(self.rssfeed["update_interval"])
            self.glade.get_widget("checkbox_obey_ttl").set_active(self.rssfeed["obey_ttl"])

    def on_button_save_clicked(self, Event=None, a=None, col=None):
        name = self.glade.get_widget("txt_name").get_text()
        url = self.glade.get_widget("txt_url").get_text()
        update_interval = self.glade.get_widget("spinbutton_updatetime").get_value()
        obey_ttl = self.glade.get_widget("checkbox_obey_ttl").get_active()

        self.rssfeed["name"] = name
        self.rssfeed["url"] = url
        self.rssfeed["update_interval"] = int(update_interval)
        self.rssfeed["site"] = urlparse(url).netloc
        self.rssfeed["obey_ttl"] = obey_ttl

        self.gtkUI.save_rssfeed(self.rssfeed)
        self.dialog.destroy()

    def on_info(self):
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_CLOSE, "You must select a RSS Feed")
        md.run()
        md.destroy()

    def on_button_cancel_clicked(self, Event=None):
        self.dialog.destroy()
