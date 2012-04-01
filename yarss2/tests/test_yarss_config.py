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

import deluge.configmanager
import tempfile
import os

import os.path

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

        config.verify_config()

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

        config.insert_missing_dict_values(subscription_del, default_subscription, level=1)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)
        
        subscription_del = yarss2.yarss_config.get_fresh_subscription_config()
        # Remove some keys from default subscription
        del subscription_del["regex_include"]
        del subscription_del["email_notifications"]

        conf = {"0": subscription_del}
        config.insert_missing_dict_values(conf, default_subscription, level=2)
        key_diff = set(default_subscription.keys()) - set(subscription_del.keys())
        self.assertTrue(not key_diff)

