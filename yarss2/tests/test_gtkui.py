# -*- coding: utf-8 -*-
#
# test_gtkui.py
#
# Copyright (C) 2012 Bro
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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

import re

from twisted.trial import unittest

from yarss2 import yarss_config
from yarss2.util.logger import Logger
from yarss2.gtkui.gtkui import GtkUI
import yarss2.gtkui.gtkui
import test_gtkui

yarss2.gtkui.gtkui.component = test_gtkui

class DummyComponent(object):
    def add_page(self, name, widget):
        pass

    def register_hook(self, name, func):
        pass

def get(string):
    return DummyComponent()

class GtkUITestCase(unittest.TestCase):

    def setUp(self):
        self.log = Logger()
        self.gtkui = GtkUI("YaRSS2")
        self.gtkui.createUI()

    def test_on_button_send_email_clicked(self):
        email_messages = {}
        email_messages["0"] = yarss_config.get_fresh_message_config()
        email_messages["0"]["name"] = "Name"
        email_messages["0"]["subject"] = "Subject"
        self.gtkui.email_messages = email_messages
        self.gtkui.email_config = yarss_config.get_fresh_email_config()
        #self.email_messages_treeview
        self.gtkui.update_email_messages_list(self.gtkui.email_messages_store)
        # Set selected
        self.gtkui.email_messages_treeview.set_cursor(0)
        self.gtkui.on_button_send_email_clicked(None)
