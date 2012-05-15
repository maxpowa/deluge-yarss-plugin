# -*- coding: utf-8 -*-
#
# test_dialog_subscription.py
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

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log
import deluge.common
json = deluge.common.json

from yarss2.gtkui.dialog_subscription import DialogSubscription
import yarss2.common
from yarss2 import yarss_config

import common

class DialogSubscriptionTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_rssfeed_selected(self):
        def verify_result(empty, subscription_dialog):
            stored_items = common.load_json_testdata()
            result = self.get_rssfeed_store_content(subscription_dialog)
            self.assertTrue(self.compare_dicts_content(stored_items, result))

        d = self.run_select_rssfeed(callback_func=verify_result)
        return d

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
                if result[k]["matches"]:
                    match_count += 1
                    self.assertTrue(p.search(result[k]["title"]))
            self.assertEquals(match_count, expected_match_count)

        d = self.run_select_rssfeed(subscription_config=subscription_config, callback_func=verify_result)
        return d

    def run_select_rssfeed(self, subscription_config=None, callback_func=None):
        config = self.get_test_config()

        if not subscription_config:
            subscription_config = yarss_config.get_fresh_subscription_config()
        subscription_dialog = DialogSubscription(None, subscription_config, 
                                                 config["rssfeeds"], 
                                                 [],  #self.get_move_completed_list(), 
                                                 {}, #self.email_messages,
                                                 {}) #self.cookies)
        subscription_dialog.setup()
    
        def pass_func(*arg):
            pass

        # Override the default selection callback
        subscription_dialog.method_perform_rssfeed_selection = pass_func
        
        # Sets the index 0 of rssfeed combox activated.
        rssfeeds_combobox = subscription_dialog.glade.get_widget("combobox_rssfeeds")
        rssfeeds_combobox.set_active(1)
        
        d = subscription_dialog.perform_rssfeed_selection()
        d.addCallback(callback_func, subscription_dialog)
        return d

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

        d = self.run_select_rssfeed(callback_func=run_search_test)
        return d

    def compare_dicts_content(self, dict1, dict2):
        """Compares the content of two dictionaries. 
        If all the items of dict1 are found in dict2, returns True
        Returns True if there are items in dict2 that does not exist in dict1
        """
        for k1 in dict1.keys():
            found = False
            for k2 in dict2.keys():
                if common.dicts_equals(dict1[k1], dict2[k2]):
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
            item["updated_datetime"] = yarss2.common.isodate_to_datetime(store.get_value(it, 2))
            item["link"] = store.get_value(it, 3)
            result[str(counter)] = item
            counter += 1
            it = store.iter_next(it)
        return result

    def get_test_config(self):
        config =  yarss2.yarss_config.default_prefs()
        file_url = yarss2.common.get_resource(common.testdata_rssfeed_filename, path="tests")
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
