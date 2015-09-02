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

import yarss2.yarss_config
from yarss2.util.logger import Logger
from yarss2.gtkui.dialog_cookie import DialogCookie


class DummyClass(object):

    def __init__(self):
        self.cookie_data = None

    def destroy(self):
        pass

    def save_cookie(self, cookie_data):
        self.cookie_data = cookie_data


class DialogCookiesTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.log = Logger()
        self.test_cookie = yarss2.yarss_config.get_fresh_cookie_config()

    def test_create(self):
        """Just test that the code runs"""
        dialog = DialogCookie(None, self.test_cookie)
        self.assertTrue(dialog is not None)

    def test_on_button_save_clicked(self):
        """Just test that the code runs"""
        dummy = DummyClass()
        self.test_cookie["active"] = True
        self.test_cookie["site"] = "Site url"

        cookie_copy = copy.deepcopy(self.test_cookie)
        dialog = DialogCookie(dummy, cookie_copy)
        dialog.dialog = dummy
        dialog.glade.get_widget("text_key").set_text("key1")
        dialog.glade.get_widget("text_value").set_text("value1")
        dialog.on_button_add_cookie_data_clicked(None)
        dialog.on_button_save_clicked(None)

        self.test_cookie["value"]["key1"] = "value1"
        self.assertEquals(self.test_cookie, dummy.cookie_data)
