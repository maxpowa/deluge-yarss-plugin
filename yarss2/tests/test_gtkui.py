# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest
import twisted.internet.defer as defer

from yarss2 import yarss_config
from yarss2.util.logger import Logger
from yarss2.gtkui.gtkui import GtkUI
import yarss2.gtkui.gtkui
import test_gtkui

from yarss2.tests import common as tests_common
from deluge.ui.client import client

import deluge.component as component

yarss2.gtkui.gtkui.component = test_gtkui


class DummyComponent(object):
    def add_page(self, name, widget):
        pass

    def register_hook(self, name, func):
        pass


def get(string):
    return DummyComponent()


class GtkUITestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.log = Logger()
        self.gtkui = GtkUI("YaRSS2")
        self.gtkui.create_ui()

    def tearDown(self):  # NOQA
        client._daemon_proxy = None
        client.__started_in_classic = False

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    def test_on_button_send_email_clicked(self):
        email_messages = {}
        email_messages["0"] = yarss_config.get_fresh_message_config()
        email_messages["0"]["name"] = "Name"
        email_messages["0"]["subject"] = "Subject"
        self.gtkui.email_messages = email_messages
        self.gtkui.email_config = yarss_config.get_fresh_email_config()
        self.gtkui.update_email_messages_list(self.gtkui.email_messages_store)
        # Set selected
        self.gtkui.email_messages_treeview.set_cursor(0)
        self.gtkui.on_button_send_email_clicked(None)


class GtkUIWithCoreTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        defer.setDebugging(True)
        tests_common.set_tmp_config_dir()
        client.start_classic_mode()
        client.core.enable_plugin("Label")

        self.log = Logger()
        self.gtkui = GtkUI("YaRSS2")
        self.gtkui.create_ui()

    def tearDown(self):  # NOQA
        client._daemon_proxy = None
        client.__started_in_classic = False

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    def test_get_labels(self):
        d = self.gtkui.plugins_enabled_changed("Label")

        def on_labels(labels):
            self.assertEquals([""], labels)
        d.addCallback(on_labels)

        # Add some labels
        client.label.add("Test-label")
        client.label.add("Test-label2")

        d = self.gtkui.plugins_enabled_changed("Label")

        def on_labels2(labels):
            self.failUnlessIn("test-label", labels)
            self.failUnlessIn("test-label2", labels)
        d.addCallback(on_labels2)
