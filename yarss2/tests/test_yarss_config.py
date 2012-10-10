# -*- coding: utf-8 -*-
#
# test_yarss_config.py
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

import yarss2.yarss_config
import common

class ConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.config = common.get_empty_test_config()

    def test_verify_config(self):
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        # Remove some keys from default subscription
        del default_subscription["regex_include"]
        del default_subscription["email_notifications"]
        # Remove key from email configuration.
        default = yarss2.yarss_config.get_fresh_email_configurations()
        del default["default_email_to_address"]

        # Main difference between these is that config["subscriptions"] contains a dictionary
        # that contins subscription dictionaries.
        # config["email_configurations"] is a dictionary containing key/value pairs directly.

        self.config.config["subscriptions"]["0"] = default_subscription
        self.config.config["email_configurations"] = default

        self.config._verify_config()

        self.assertTrue(self.config.config["subscriptions"]["0"].has_key("regex_include") and \
            type(self.config.config["subscriptions"]["0"]) is dict)

        self.assertTrue(self.config.config["email_configurations"].has_key("default_email_to_address"))

    def test_insert_missing_dict_values(self):
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        subscription_del = yarss2.yarss_config.get_fresh_subscription_config()

        # Remove some keys from default subscription
        del subscription_del["regex_include"]
        del subscription_del["email_notifications"]

        self.config._insert_missing_dict_values(subscription_del, default_subscription, level=1)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)

        subscription_del = yarss2.yarss_config.get_fresh_subscription_config()
        # Remove some keys from default subscription
        del subscription_del["regex_include"]
        del subscription_del["email_notifications"]

        conf = {"0": subscription_del}
        self.config._insert_missing_dict_values(conf, default_subscription, level=2)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)

    def test_verify_types_config_elements(self):
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        subscriptions = common.get_default_subscriptions(2)

        for i in range(2):
            subscriptions[str(i)]["name"] = None
            subscriptions[str(i)]["active"] = ""
            subscriptions[str(i)]["key"] = ""
        changed = self.config._verify_types_config_elements(subscriptions, default_subscription)
        self.assertTrue(changed)

        for i in range(2):
            self.assertEquals(subscriptions[str(i)]["name"], default_subscription["name"])
            self.assertEquals(subscriptions[str(i)]["active"], default_subscription["active"])

    def test_verify_types_values_changed(self):
        # 0 is just a key value (could be any number)
        config_key = "0"
        # Default must have a different key than the test subscription, so set to ""
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config(key="")
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)

        # Change type of the value for some keys
        #subscription_changed["name"] = u"Non default"
        subscription_changed["regex_include"] = None              # Should be unicode
        subscription_changed["email_notifications"] = []          # Should be dict
        subscription_changed["regex_include_ignorecase"] = ""     # Should be boolean
        subscription_changed["rssfeed_key"] = unicode(config_key) # Should be str
        subscription_changed["key"] = None                        # Should be str

        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        self.assertEquals(subscription_changed["regex_include"], default_subscription["regex_include"])
        self.assertEquals(subscription_changed["email_notifications"], default_subscription["email_notifications"])
        self.assertEquals(subscription_changed["regex_include_ignorecase"], default_subscription["regex_include_ignorecase"])
        self.assertEquals(subscription_changed["key"], config_key)

    def test_verify_types_values_deleted(self):
        config_key = "0"
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)

        # Remove some keys from default subscription
        subscription_changed["name"] = "Not default"
        subscription_changed["rssfeed_key"] = "0"
        del subscription_changed["regex_include"]
        del subscription_changed["email_notifications"]
        del subscription_changed["key"]

        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        self.assertEquals(subscription_changed["regex_include"], default_subscription["regex_include"])
        self.assertEquals(subscription_changed["email_notifications"], default_subscription["email_notifications"])

        # Here, the missing key value should be set to config_key, and not the default value (which doesn't exist)
        self.assertEquals(subscription_changed["key"], config_key)

        # Verify that the value of regex_exclude has been converted to unicode
        self.assertEquals(type(subscription_changed["regex_exclude"]), unicode)

    def test_verify_types_rssfeed_key_invalid_default_values(self):
        """Test if rssfeed_key is invalid in a subscription, and the subscription has the default values
        In that case, the subscription should be deleted"""
        config_key = "0"
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)

        # rssfeed_key is not an integer
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        subscription_changed["rssfeed_key"] = ""
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # Since the subscription has the default values, all values should now be deleted
        self.assertEquals(len(subscription_changed.keys()), 0)

        # rssfeed_key has invalid type
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        subscription_changed["rssfeed_key"] = True
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # Since the subscription has the default values, all values should now be deleted
        self.assertEquals(len(subscription_changed.keys()), 0)

        # rssfeed_key doesn't exist
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        del subscription_changed["rssfeed_key"]
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # Since the subscription has the default values, all values should now be deleted
        self.assertEquals(len(subscription_changed.keys()), 0)

    def test_verify_types_rssfeed_key_invalid_non_default_values(self):
        """Test if rssfeed_key is invalid in a subscription, and the subscription has NON-default values
        In that case, a dummy rssfeed should be create (if it doesn't exist), and the subscription should be given
        the rssfeed_key of the dummy"""
        config_key = "0"
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)

        # rssfeed_key is not an integer
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        subscription_changed["rssfeed_key"] = ""
        subscription_changed["name"] = u"Not default"
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # rssfeed_key should be the DUMMY_RSSFEED_KEY
        self.assertTrue(self.config.config["rssfeeds"].has_key(yarss2.yarss_config.DUMMY_RSSFEED_KEY))

        # rssfeed_key has invalid type
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        subscription_changed["rssfeed_key"] = True
        subscription_changed["name"] = u"Not default"
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # rssfeed_key should be the DUMMY_RSSFEED_KEY
        self.assertTrue(self.config.config["rssfeeds"].has_key(yarss2.yarss_config.DUMMY_RSSFEED_KEY))

        # rssfeed_key doesn't exist
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config(key=config_key)
        del subscription_changed["rssfeed_key"]
        subscription_changed["name"] = u"Not default"
        changed = self.config._verify_types(config_key, subscription_changed, default_subscription)
        self.assertTrue(changed)
        # rssfeed_key should be the DUMMY_RSSFEED_KEY
        self.assertTrue(self.config.config["rssfeeds"].has_key(yarss2.yarss_config.DUMMY_RSSFEED_KEY))

    def test_verify_config(self):
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        test_feeds = common.get_default_rssfeeds(2)
        test_subscriptions = common.get_default_subscriptions(3)
        test_subscriptions["0"]["rssfeed_key"] = "0"
        test_subscriptions["1"]["rssfeed_key"] = "0"
        test_subscriptions["0"]["name"] = True # Wrong type

        del test_subscriptions["0"]["regex_include"]
        del test_subscriptions["1"]["key"]
        del test_subscriptions["2"]["rssfeed_key"]

        self.config.config["rssfeeds"] = test_feeds
        self.config.config["subscriptions"] = test_subscriptions
        self.config._verify_config()

        # Should have the key reinserted
        self.assertEquals(test_subscriptions["1"]["key"], "1")
        # Name should be default value
        self.assertEquals(test_subscriptions["0"]["name"], default_subscription["name"])
        # regex_include should be reinserted with the default value
        self.assertTrue(test_subscriptions["0"].has_key("regex_include"))
        # The rssfeed_key should be the dummy
        self.assertEquals(test_subscriptions["2"]["rssfeed_key"], yarss2.yarss_config.DUMMY_RSSFEED_KEY)
        # The dummy should now exist in rssfeeds dict
        self.assertTrue(test_feeds.has_key(yarss2.yarss_config.DUMMY_RSSFEED_KEY))
