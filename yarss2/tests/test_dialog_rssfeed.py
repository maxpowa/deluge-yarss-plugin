# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest
import copy
from urlparse import urlparse

import yarss2.yarss_config
from yarss2.util.logger import Logger
from yarss2.gtkui.dialog_rssfeed import DialogRSSFeed


class DummyClass(object):

    def __init__(self):
        self.rssfeed = None

    def destroy(self):
        pass

    def save_rssfeed(self, rssfeed):
        pass


class DialogRSSFeedTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.log = Logger()
        self.test_rssfeed = yarss2.yarss_config.get_fresh_rssfeed_config()

    def test_create(self):
        """Just test that the code runs"""
        DialogRSSFeed(None, self.test_rssfeed)

    def test_on_button_save_clicked(self):
        """Just test that the code runs"""
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
