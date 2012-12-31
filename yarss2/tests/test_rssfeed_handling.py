# -*- coding: utf-8 -*-
#
# test_rssfeed_handling.py
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

import datetime
import threading

import twisted.internet.defer as defer
from twisted.trial import unittest

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log

import yarss2.util.common
import yarss2.yarss_config
from yarss2.rssfeed_handling import RSSFeedHandler

import common

class RSSFeedHandlingTestCase(unittest.TestCase):

    def setUp(self):
        self.log = log
        self.rssfeedhandler = RSSFeedHandler(self.log)

    def test_get_rssfeed_parsed(self):
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
        rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments"}
        site_cookies = {"uid": "18463", "passkey": "b830f87d023037f9393749s932"}

        parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=site_cookies)

        # When needing to dump the result in json format
        #common.json_dump(parsed_feed["items"], "freebsd_rss_items_dump2.json")

        self.assertTrue(parsed_feed.has_key("items"))
        items = parsed_feed["items"]
        stored_items = common.load_json_testdata()
        self.assertTrue(yarss2.util.common.dicts_equals(items, stored_items, debug=False))
        self.assertEquals(parsed_feed["cookie_header"], {'Cookie': 'uid=18463; passkey=b830f87d023037f9393749s932'})

    def test_get_link(self):
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
        from yarss2.lib.feedparser import feedparser
        parsed_feed = feedparser.parse(file_url)
        item = None
        for e in parsed_feed["items"]:
            item = e
            break
        # Item has enclosure, so it should use that link
        self.assertEquals(self.rssfeedhandler.get_link(item), item.enclosures[0]["href"])
        del item["links"][:]
        # Item no longer has enclosures, so it should return the regular link
        self.assertEquals(self.rssfeedhandler.get_link(item), item["link"])

    def test_get_size(self):
        file_url = yarss2.util.common.get_resource("t1.rss", path="tests/data/feeds/")
        from yarss2.lib.feedparser import feedparser
        parsed_feed = feedparser.parse(file_url)

        size = self.rssfeedhandler.get_size(parsed_feed["items"][0])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (4541927915.52, u'4.23 GB'))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][1])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (402349096.96, u'383.71 MB'))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][2])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (857007476))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][3])
        self.assertEquals(len(size), 2)
        self.assertEquals(size[0], (14353107637))
        self.assertEquals(size[1], (13529146982.4, u'12.6 GB'))

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
        matching, msg  = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()))

        # Also make sure the items in 'matching' correspond to the matching items in rssfeed_parsed
        count = 0
        for key in rssfeed_parsed.keys():
            if rssfeed_parsed[key]["matches"]:
                self.assertTrue(matching.has_key(key), "The matches dict does not contain the matching key '%s'" % key)
                count += 1
        self.assertEquals(count, len(matching.keys()),
                          "The number of items in matches dict (%d) does not match the number of matching items (%d)" % (count, len(matching.keys())))

        options["regex_include_ignorecase"] = False
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 1)

        #options["regex_include_ignorecase"] = True
        options["regex_exclude"] = "i386"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 2)

        # Fresh options
        options, rssfeed_parsed = self.get_default_rssfeeds_dict()

        # Custom line with unicode characters, norwegian ø and å, as well as Latin Small Letter Lambda with stroke
        options["custom_text_lines"] = [u"Test line with æ and å, as well as ƛ"]
        options["regex_include"] = "æ"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (15, 17))

        options["regex_include"] = "with.*ƛ"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (10, 39))

        # Test exclude span
        options["regex_include"] = ".*"
        options["regex_exclude"] = "line.*å"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        for key in rssfeed_parsed.keys():
            if not rssfeed_parsed[key]["matches"]:
                self.assertEquals(rssfeed_parsed[key]["title"], options["custom_text_lines"][0])
                self.assertEquals(rssfeed_parsed[key]["regex_exclude_match"], (5, 24))
                break

    def test_fetch_feed_torrents(self):
        config = common.get_test_config_dict()                                # 0 is the rssfeed key
        matche_result = self.rssfeedhandler.fetch_feed_torrents(config, "0")
        matches = matche_result["matching_torrents"]
        self.assertTrue(len(matches) == 3)

    #def test_label(self):
    #    #from deluge.ui.client import sclient
    #    #sclient.set_core_uri()
    #    #print sclient.get_enabled_plugins()
    #    import deluge.component as component
    #    from deluge.core.pluginmanager import PluginManager
    #    from deluge.ui.client import client
    #    plugins = PluginManager(self)
    #    # Enable plugins
    #    plugins.start()
    #
    #    print "Enabled   plugins:", plugins.get_enabled_plugins()
    #    print "Available plugins:", plugins.get_available_plugins()
    #    if "Label" in plugins.get_available_plugins():
    #        print "Label plugin found"
    #
    #    plugins.enable_plugin("Label")
    #
    #    print "info:", plugins.get_plugin_info("Label")
    #    print "Enabled   plugins:", plugins.get_enabled_plugins()
    #    #client.label.enable()
    #    #print "label:", client.label.get_labels()


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

