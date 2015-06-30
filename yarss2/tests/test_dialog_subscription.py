# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest
import datetime
import gtk
import re

from twisted.internet import defer

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log
import deluge.component as component
import deluge.common
json = deluge.common.json

import common

import yarss2.util.common
from yarss2 import yarss_config

import yarss2.gtkui.dialog_subscription

import deluge.ui.client
from deluge.ui.client import Client

from yarss2.gtkui.dialog_subscription import DialogSubscription
from yarss2.util.logger import Logger


import deluge.configmanager
import time

class DialogSubscriptionTestCase(unittest.TestCase):

    def setUp(self):
        self.log = Logger()
        deluge.ui.client.client = Client()
        self.client = deluge.ui.client.client
        self.client.start_classic_mode()

    def tearDown(self):
        d = component.shutdown()
        # Components aren't removed from registry in component.shutdown...
        # so must do that manually
        for c_name in component._ComponentRegistry.components.keys():
            del component._ComponentRegistry.components[c_name]
        return d

    def test_rssfeed_selected(self):
        #deluge.configmanager.set_config_dir("/home/bro/programmer/deluge/deluge-yarss-plugin/yarss2/tests/config")
        yarss2.gtkui.dialog_subscription.client = self.client

        def verify_result(empty, subscription_dialog):
            stored_items = common.load_json_testdata()
            result = self.get_rssfeed_store_content(subscription_dialog)
            self.assertTrue(self.compare_dicts_content(stored_items, result))
        defered = self.run_select_rssfeed(callback_func=verify_result)
        return defered

    def test_select_rssfeed_with_search(self):
        subscription_config = yarss_config.get_fresh_subscription_config()
        search_regex = "bootonly"
        expected_match_count = 6
        subscription_config["regex_include"] = search_regex

        def verify_result(empty, subscription_dialog):
            result = self.get_rssfeed_store_content(subscription_dialog)
            p = re.compile(search_regex)
            match_count = 0
            for k in result:
                if result[k]["matches"] == True:
                    match_count += 1
                    self.assertTrue(p.search(result[k]["title"]))
            self.assertEquals(match_count, expected_match_count)

        defered = self.run_select_rssfeed(subscription_config=subscription_config, callback_func=verify_result)
        return defered

    def run_select_rssfeed(self, subscription_config=None, callback_func=None):
        config = self.get_test_config()

        if not subscription_config:
            subscription_config = yarss_config.get_fresh_subscription_config()
        subscription_dialog = DialogSubscription(None, # GTKUI
                                                 self.log, # logger
                                                 subscription_config,
                                                 config["rssfeeds"],
                                                 [], #self.get_move_completed_list(),
                                                 [], #self.get_download_location_list(),
                                                 {}, #self.email_messages,
                                                 {}) #self.cookies)
        subscription_dialog.setup()

        def pass_func(*arg):
            #pass
            print "PASS FUNC"
            return defer.Deferred()

        class DialogWrapper(object):
            def __init__(self, dialog):
                self.dialog = dialog
            def get_visible(self):
                return True

        subscription_dialog.dialog = DialogWrapper(subscription_dialog.dialog)

        # Override the default selection callback
        #subscription_dialog.method_perform_rssfeed_selection = pass_func
        subscription_dialog.perform_rssfeed_selection = pass_func

        # Sets the index 0 of rssfeed combox activated.
        rssfeeds_combobox = subscription_dialog.glade.get_widget("combobox_rssfeeds")
        rssfeeds_combobox.set_active(1)

        #defered = subscription_dialog.perform_rssfeed_selection()
        defered = subscription_dialog.method_perform_rssfeed_selection()
        defered.addCallback(callback_func, subscription_dialog)
        return defered

    def test_search(self):
        def run_search_test(empty, dialog_subscription):
            subscription_config = yarss_config.get_fresh_subscription_config()
            include_regex = ".*"
            exclude_regex = "64|MEMstick"
            expected_match_count = 7
            subscription_config["regex_include"] = include_regex
            subscription_config["regex_exclude"] = exclude_regex

            # Loading new config, and perform search
            dialog_subscription.subscription_data = subscription_config
            dialog_subscription.load_basic_fields_data()
            dialog_subscription.perform_search()

            result = self.get_rssfeed_store_content(dialog_subscription)

            p_include = re.compile(include_regex, re.IGNORECASE if subscription_config["regex_include_ignorecase"] else 0)
            p_exclude = re.compile(exclude_regex, re.IGNORECASE if subscription_config["regex_exclude_ignorecase"] else 0)
            match_count = 0
            for k in result:
                if result[k]["matches"]:
                    match_count += 1
                    self.assertTrue(p_include.search(result[k]["title"]), "Expected '%s' to in '%s'" % (include_regex, result[k]["title"]))
                else:
                    self.assertTrue(p_exclude.search(result[k]["title"]), "Expected '%s' to in '%s'" % (exclude_regex, result[k]["title"]))
            self.assertEquals(match_count, expected_match_count)

        defered = self.run_select_rssfeed(callback_func=run_search_test)
        return defered

    def compare_dicts_content(self, dict1, dict2):
        """Compares the content of two dictionaries.
        If all the items of dict1 are found in dict2, returns True
        Returns True if there are items in dict2 that does not exist in dict1
        """
        for k1 in dict1.keys():
            found = False
            for k2 in dict2.keys():
                if yarss2.util.common.dicts_equals(dict1[k1], dict2[k2]):
                    break
            else:
                return False
        return True

    def get_rssfeed_store_content(self, subscription_dialog):
        store = subscription_dialog.matching_store
        it = store.get_iter_first()
        result = {}
        counter = 0

        while it:
            item = {}
            item["matches"] = store.get_value(it, 0)
            item["title"] = store.get_value(it, 1)
            item["updated"] = store.get_value(it, 2)
            item["updated_datetime"] = yarss2.util.common.isodate_to_datetime(store.get_value(it, 2))
            item["link"] = store.get_value(it, 3)
            result[str(counter)] = item
            counter += 1
            it = store.iter_next(it)
        return result

    def get_test_config(self):
        config =  yarss2.yarss_config.default_prefs()
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests")
        rssfeeds = common.get_default_rssfeeds(2)
        subscriptions = common.get_default_subscriptions(5)

        rssfeeds["0"]["name"] = "Test RSS Feed"
        rssfeeds["0"]["url"] = file_url
        rssfeeds["1"]["name"] = "Test RSS Feed2"
        rssfeeds["1"]["active"] = False

        subscriptions["0"]["name"] = "Matching subscription"
        subscriptions["0"]["regex_include"] = "sparc64"
        subscriptions["1"]["name"] = "Non-matching subscription"
        subscriptions["1"]["regex_include"] = None
        subscriptions["2"]["name"] = "Inactive subscription"
        subscriptions["2"]["active"] = False
        subscriptions["3"]["name"] = "Update_time too new"
        subscriptions["3"]["last_update"] = datetime.datetime.now().isoformat()
        subscriptions["4"]["name"] = "Wrong rsskey subscription"
        subscriptions["4"]["rssfeed_key"] = "1"

        config["rssfeeds"] = rssfeeds
        config["subscriptions"] = subscriptions
        return config

    def test_save_subscription(self):
        subscription_title = "Test subscription"
        regex_include = "Regex"
        config = self.get_test_config()

        class TestGTKUI(unittest.TestCase):
            def save_subscription(self, subscription_data):
                self.assertEquals(subscription_data["name"], subscription_title)
                self.assertEquals(subscription_data["regex_include"], regex_include)
                self.assertEquals(subscription_data["add_torrents_in_paused_state"], "True")
                self.assertEquals(subscription_data["auto_managed"], "False")
                self.assertEquals(subscription_data["sequential_download"], "Default")
                self.assertEquals(subscription_data["prioritize_first_last_pieces"], "Default")

        subscription_config = yarss_config.get_fresh_subscription_config()
        subscription_dialog = DialogSubscription(TestGTKUI(), # GTKUI
                                                 self.log, # logger
                                                 subscription_config,
                                                 config["rssfeeds"],
                                                 [], #self.get_move_completed_list(),
                                                 [], #self.get_download_location_list(),
                                                 {}, #self.email_messages,
                                                 {}) #self.cookies)
        subscription_dialog.setup()
        subscription_dialog.glade.get_widget("txt_name").set_text(subscription_title)
        subscription_dialog.glade.get_widget("txt_regex_include").set_text(regex_include)
        subscription_dialog.glade.get_widget("checkbox_add_torrents_in_paused_state_default").set_active(False)
        subscription_dialog.glade.get_widget("checkbox_add_torrents_in_paused_state").set_active(True)
        subscription_dialog.glade.get_widget("checkbutton_auto_managed_default").set_active(False)
        subscription_dialog.glade.get_widget("checkbutton_auto_managed").set_active(False)
        subscription_dialog.glade.get_widget("checkbutton_sequential_download_default").set_active(True)
        subscription_dialog.glade.get_widget("checkbutton_sequential_download").set_active(False)
        subscription_dialog.glade.get_widget("checkbutton_prioritize_first_last_default").set_active(True)
        subscription_dialog.glade.get_widget("checkbutton_prioritize_first_last").set_active(True)

        # Sets the index 0 of rssfeed combox activated.
        rssfeeds_combobox = subscription_dialog.glade.get_widget("combobox_rssfeeds")
        rssfeeds_combobox.set_active(1)
        subscription_dialog.save_subscription_data()
