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
import re
from urlparse import urlparse

import deluge.component as component

from yarss2.util.common import get_resource
import yarss2.yarss_config


class DialogRSSFeed():

    def __init__(self, gtkui, rssfeed):
        self.gtkUI = gtkui
        self.rssfeed = rssfeed

        self.glade = gtk.glade.XML(get_resource("dialog_rssfeed.glade"))
        self.glade.signal_autoconnect({
            "on_button_cancel_clicked": self.on_button_cancel_clicked,
            "on_button_save_clicked": self.on_button_save_clicked
        })
        self.populate_data_fields()

    def show(self):
        self.dialog = self.glade.get_widget("dialog_rssfeed")
        self.dialog.set_title("Edit Feed" if "key" in self.rssfeed else "Add Feed")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
        # self.glade.get_widget("spinbutton_updatetime").set_range(1, 30)
        self.dialog.run()

    def populate_data_fields(self):
        if self.rssfeed:
            self.glade.get_widget("txt_name").set_text(self.rssfeed["name"])
            self.glade.get_widget("txt_url").set_text(self.rssfeed["url"])
            self.glade.get_widget("spinbutton_updatetime").set_value(self.rssfeed["update_interval"])
            self.glade.get_widget("checkbox_obey_ttl").set_active(self.rssfeed["obey_ttl"])

            # Disable the fields field
            if "key" in self.rssfeed and self.rssfeed["key"] == yarss2.yarss_config.DUMMY_RSSFEED_KEY:
                self.glade.get_widget("txt_name").set_property("editable", False)
                self.glade.get_widget("txt_name").unset_flags(gtk.CAN_FOCUS)
                self.glade.get_widget("txt_url").set_property("editable", False)
                self.glade.get_widget("txt_url").unset_flags(gtk.CAN_FOCUS)
                self.glade.get_widget("spinbutton_updatetime").set_sensitive(False)
                self.glade.get_widget("checkbox_obey_ttl").set_active(False)
                self.glade.get_widget("checkbox_obey_ttl").set_sensitive(False)
                self.glade.get_widget("button_save").set_sensitive(False)

    def on_button_save_clicked(self, event=None, a=None, col=None):
        name = self.glade.get_widget("txt_name").get_text()
        url = self.glade.get_widget("txt_url").get_text()
        update_interval = self.glade.get_widget("spinbutton_updatetime").get_value()
        obey_ttl = self.glade.get_widget("checkbox_obey_ttl").get_active()

        allowed_types = ('http', 'https', 'ftp', 'file', 'feed')
        if not urlparse(url)[0] in allowed_types:
            md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_CLOSE, "The address must begin with one of: %s" %
                                   (", ".join(t for t in allowed_types)))
            md.run()
            md.destroy()
            return
        self.rssfeed["name"] = name
        # Handle spaces in url
        self.rssfeed["url"] = re.sub('\s', '%20', url.strip())
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

    def on_button_cancel_clicked(self, event=None):
        self.dialog.destroy()
