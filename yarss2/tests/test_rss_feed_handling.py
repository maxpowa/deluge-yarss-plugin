# -*- coding: utf-8 -*-
#
# test_rss_feed_handling.py
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

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log

import yarss2.common
import yarss2.yarss_config
from yarss2.rssfeed_handling import get_rssfeed_parsed, update_rssfeeds_dict_matching, \
    fetch_subscription_torrents

import common

class RSSFeedHandlingTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_rssfeed_parsed(self):
        file_url = yarss2.common.get_resource(common.testdata_rssfeed_filename, path="tests")
        
        rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments"}
        parsed_feed = get_rssfeed_parsed(rssfeed_data)

        self.assertTrue(parsed_feed.has_key("items"))

        #self.json_dump(parsed_feed["items"], self.rss_itmes_json_filename)

        items = parsed_feed["items"]
        stored_items = common.load_json_testdata()
        self.assertTrue(common.dicts_equals(items, stored_items))

    def get_default_rssfeeds_dict(self):
        match_option_dict = {}
        match_option_dict["regex_include"] = ""
        match_option_dict["regex_exclude"] = ""
        match_option_dict["regex_include_ignorecase"] = True
        match_option_dict["regex_exclude_ignorecase"] = True
        match_option_dict["custom_text_lines"] = None
        
        rssfeed_matching = {}
        rssfeed_matching["0"] = {"matches": False, "link": "", "title": "FreeBSD-9.0-RELEASE-amd64-all"}
        rssfeed_matching["1"] = {"matches": False, "link": "", "title": "FreeBSD-9.0-RELEASE-i386-all"}
        rssfeed_matching["2"] = {"matches": False, "link": "", "title": "fREEbsd-9.0-RELEASE-i386-all"}
        return match_option_dict, rssfeed_matching

    def test_update_rssfeeds_dict_matching(self):
        options, rssfeed_parsed = self.get_default_rssfeeds_dict()
        options["regex_include"] = "FreeBSD"
        matching, msg  = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()))
        
        # Also make sure the items in matching correspond to the matching items in rssfeed_parsed
        count = 0
        for key in rssfeed_parsed.keys():
            if rssfeed_parsed[key]["matches"]:
                self.assertTrue(matching.has_key(key), "The matches dict does not contain the matching key '%s'" % key)
                count += 1
        self.assertEquals(count, len(matching.keys()), 
                          "The number of items in matches dict (%d) does not match the number of matching items (%d)" % (count, len(matching.keys())))

        options["regex_include_ignorecase"] = False
        matching, msg = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 1)
        
        #options["regex_include_ignorecase"] = True
        options["regex_exclude"] = "i386"
        matching, msg = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 2)
       
        # Fresh options
        options, rssfeed_parsed = self.get_default_rssfeeds_dict()

        # Custom line with unicode characters, norwegian ø and å, as well as Latin Small Letter Lambda with stroke
        options["custom_text_lines"] = [u"Test line with æ and å, as well as ƛ"]
        options["regex_include"] = "æ"
        matching, msg = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (15, 17))

        options["regex_include"] = "with.*ƛ"
        matching, msg = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (10, 39))
            
        # Test exclude span
        options["regex_include"] = ".*"
        options["regex_exclude"] = "line.*å"
        matching, msg = update_rssfeeds_dict_matching(rssfeed_parsed, options)
        for key in rssfeed_parsed.keys():
            if not rssfeed_parsed[key]["matches"]:
                self.assertEquals(rssfeed_parsed[key]["title"], options["custom_text_lines"][0])
                self.assertEquals(rssfeed_parsed[key]["regex_exclude_match"], (5, 24))
                break

    def test_fetch_subscription_torrents(self):
        config = self.get_test_config()
        matches = fetch_subscription_torrents(config, "0")
        self.assertTrue(len(matches) == 3)


####################################
## Helper methods for test data
####################################

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

#Name:  FreeBSD-9.0-RELEASE-amd64-all
#Name:  FreeBSD-9.0-RELEASE-i386-all
#Name:  FreeBSD-9.0-RELEASE-ia64-all
#Name:  FreeBSD-9.0-RELEASE-powerpc-all
#Name:  FreeBSD-9.0-RELEASE-powerpc64-all
#Name:  FreeBSD-9.0-RELEASE-sparc64-all
#Name:  FreeBSD-9.0-RELEASE-amd64-bootonly
#Name:  FreeBSD-9.0-RELEASE-amd64-disc1
#Name:  FreeBSD-9.0-RELEASE-amd64-dvd1
#Name:  FreeBSD-9.0-RELEASE-amd64-memstick
#Name:  FreeBSD-9.0-RELEASE-i386-bootonly
#Name:  FreeBSD-9.0-RELEASE-i386-disc1
#Name:  FreeBSD-9.0-RELEASE-i386-dvd1
#Name:  FreeBSD-9.0-RELEASE-i386-memstick
#Name:  FreeBSD-9.0-RELEASE-ia64-bootonly
#Name:  FreeBSD-9.0-RELEASE-ia64-memstick
#Name:  FreeBSD-9.0-RELEASE-ia64-release
#Name:  FreeBSD-9.0-RELEASE-powerpc-bootonly
#Name:  FreeBSD-9.0-RELEASE-powerpc-memstick
#Name:  FreeBSD-9.0-RELEASE-powerpc-release
#Name:  FreeBSD-9.0-RELEASE-powerpc64-bootonly
#Name:  FreeBSD-9.0-RELEASE-powerpc64-memstick
#Name:  FreeBSD-9.0-RELEASE-powerpc64-release
#Name:  FreeBSD-9.0-RELEASE-sparc64-bootonly
#Name:  FreeBSD-9.0-RELEASE-sparc64-disc1
        
