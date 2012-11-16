# -*- coding: utf-8 -*-
#
# test_dialog_rssfeed.py
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

from twisted.trial import unittest
import datetime
import gtk
import re
import copy

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log
import deluge.common
json = deluge.common.json

from yarss2.gtkui.dialog_subscription import DialogSubscription
import yarss2.common
from yarss2 import yarss_config
from yarss2.logger import Logger
from yarss2.gtkui.dialog_rssfeed import DialogRSSFeed

from urlparse import urlparse


import common
import yarss2.common

class DummyClass(object):

    def __init__(self):
        self.rssfeed = None

    def destroy(self):
        pass

    def save_rssfeed(self, rssfeed):
        pass
        #if self.rssfeed:
        #    dicts_equals(dict1, dict2)

class DialogRSSFeedTestCase(unittest.TestCase):

    def setUp(self):
        self.log = Logger()
        self.test_rssfeed = yarss2.yarss_config.get_fresh_rssfeed_config()

    def test_create(self):
        """Just test that the code runs"""
        dialog = DialogRSSFeed(None, self.test_rssfeed)

    def test_on_button_save_clicked(self):
        """Just test that the code runs"""
        #yarss2.yarss_config.get_fresh_rssfeed_config(key="0")
        dummy = DummyClass()
        rssfeed = yarss2.yarss_config.get_fresh_rssfeed_config()
        rssfeed["name"] = "Test"
        rssfeed["url"] = "http://test"
        rssfeed["update_interval"] = int(10)
        rssfeed["site"] = urlparse("http:/test.site.com/blabla/blalba.php").netloc
        rssfeed["obey_ttl"] = False

        rssfeed_copy = copy.copy(rssfeed)
        rssfeed_copy["name"] = "Test2"
        dummy.rssfeed = rssfeed_copy

        dialog = DialogRSSFeed(dummy, rssfeed)
        dialog.dialog = dummy
        dialog.glade.get_widget("txt_name").set_text("Test2")
        dialog.on_button_save_clicked()

        # Should test the values that are saved
