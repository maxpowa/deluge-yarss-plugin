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
        pass

    def test_verify_config(self):
        config = common.get_empty_test_config()

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

        config.config["subscriptions"]["0"] = default_subscription
        config.config["email_configurations"] = default

        config._verify_config()

        self.assertTrue(config.config["subscriptions"]["0"].has_key("regex_include") and \
            type(config.config["subscriptions"]["0"]) is dict)

        self.assertTrue(config.config["email_configurations"].has_key("default_email_to_address"))

    def test_insert_missing_dict_values(self):
        config = common.get_empty_test_config()

        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        subscription_del = yarss2.yarss_config.get_fresh_subscription_config()

        # Remove some keys from default subscription
        del subscription_del["regex_include"]
        del subscription_del["email_notifications"]

        config._insert_missing_dict_values(subscription_del, default_subscription, level=1)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)

        subscription_del = yarss2.yarss_config.get_fresh_subscription_config()
        # Remove some keys from default subscription
        del subscription_del["regex_include"]
        del subscription_del["email_notifications"]

        conf = {"0": subscription_del}
        config._insert_missing_dict_values(conf, default_subscription, level=2)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)

    def test_very_types_config_elements(self):
        config = common.get_empty_test_config()
        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        subscriptions = common.get_default_subscriptions(5)

        for i in range(5):
            subscriptions[str(i)]["name"] = None
            subscriptions[str(i)]["active"] = ""
        config._very_types_config_elements(subscriptions, default_subscription)

        for i in range(5):
            self.assertEquals(subscriptions[str(i)]["name"], default_subscription["name"])
            self.assertEquals(subscriptions[str(i)]["active"], default_subscription["active"])

    def test_verify_types(self):
        config = common.get_empty_test_config()

        default_subscription = yarss2.yarss_config.get_fresh_subscription_config()
        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config()

        # Change type of the value for some keys
        subscription_changed["regex_include"] = None
        subscription_changed["email_notifications"] = []
        subscription_changed["regex_include_ignorecase"] = ""

        config._verify_types(subscription_changed, default_subscription)
        self.assertEquals(subscription_changed["regex_include"], default_subscription["regex_include"])
        self.assertEquals(subscription_changed["email_notifications"], default_subscription["email_notifications"])
        self.assertEquals(subscription_changed["regex_include_ignorecase"], default_subscription["regex_include_ignorecase"])

        subscription_changed = yarss2.yarss_config.get_fresh_subscription_config()
        # Remove some keys from default subscription
        subscription_changed["regex_include"]
        subscription_changed["email_notifications"]

        conf = {"0": subscription_changed}
        config._insert_missing_dict_values(conf, default_subscription, level=2)
        key_diff = set(default_subscription.keys()) - set(subscription_changed.keys())
        self.assertTrue(not key_diff)
