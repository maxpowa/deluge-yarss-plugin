# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest

from deluge.log import LOG

import yarss2.util.common
import yarss2.yarss_config
from yarss2.rssfeed_handling import RSSFeedHandler

import common


class RSSFeedHandlingTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.log = LOG
        self.rssfeedhandler = RSSFeedHandler(self.log)

    def test_get_rssfeed_parsed(self):
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
        rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments",
                        "prefer_magnet": False}
        site_cookies = {"uid": "18463", "passkey": "b830f87d023037f9393749s932"}
        user_agent = "User_agent_test"
        parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=site_cookies,
                                                             user_agent=user_agent)

        # When needing to dump the result in json format
        # common.json_dump(parsed_feed["items"], "freebsd_rss_items_dump2.json")

        self.assertTrue("items" in parsed_feed)
        items = parsed_feed["items"]
        stored_items = common.load_json_testdata()
        self.assertTrue(yarss2.util.common.dicts_equals(items, stored_items, debug=False))
        self.assertEquals(sorted(parsed_feed["cookie_header"]['Cookie'].split("; ")),
                          ['passkey=b830f87d023037f9393749s932', 'uid=18463'])
        self.assertEquals(parsed_feed["user_agent"], user_agent)

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
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()))

        # Also make sure the items in 'matching' correspond to the matching items in rssfeed_parsed
        count = 0
        for key in rssfeed_parsed.keys():
            if rssfeed_parsed[key]["matches"]:
                self.assertTrue(key in matching, "The matches dict does not contain the matching key '%s'" % key)
                count += 1
        self.assertEquals(count, len(matching.keys()),
                          "The number of items in matches dict (%d) does not"
                          " match the number of matching items (%d)" % (count, len(matching.keys())))

        # Try again with regex_include_ignorecase=False
        options["regex_include_ignorecase"] = False
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 1)

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
        config = common.get_test_config_dict()
        matche_result = self.rssfeedhandler.fetch_feed_torrents(config, "0")  # 0 is the rssfeed key
        matches = matche_result["matching_torrents"]
        self.assertTrue(len(matches) == 3)

    def test_fetch_feed_torrents_custom_user_agent(self):
        config = common.get_test_config_dict()
        custom_user_agent = "TEST AGENT"
        config["rssfeeds"]["0"]["user_agent"] = custom_user_agent
        matche_result = self.rssfeedhandler.fetch_feed_torrents(config, "0")  # 0 is the rssfeed key
        self.assertEquals(matche_result["user_agent"], custom_user_agent)

    def test_feedparser_dates(self):
        file_url = yarss2.util.common.get_resource("rss_with_special_dates.rss", path="tests/data/feeds/")
        from yarss2.lib.feedparser import feedparser
        parsed_feed = feedparser.parse(file_url)

        for item in parsed_feed['items']:
            # Some RSS feeds do not have a proper timestamp
            if 'published_parsed' in item:
                published_parsed = item['published_parsed']
                import time
                test_val = time.struct_time((2014, 4, 10, 3, 44, 14, 3, 100, 0))
                self.assertEquals(test_val, published_parsed)
                break

    def test_get_rssfeed_parsed_no_items(self):
        file_url = yarss2.util.common.get_resource("feed_no_items_issue15.rss", path="tests/data/feeds/")
        rssfeed_data = {"name": "Test", "url": file_url}
        parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data)
        self.assertTrue("items" not in parsed_feed)

    def test_get_rssfeed_parsed_datetime_no_timezone(self):
        file_url = yarss2.util.common.get_resource("rss_datetime_parse_no_timezone.rss", path="tests/data/feeds/")
        rssfeed_data = {"name": "Test", "url": file_url}
        parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data)
        self.assertTrue("items" in parsed_feed)

    # def test_test_feedparser_parse(self):
    #     #file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
    #     from yarss2.lib.feedparser import feedparser
    #     file_url = ""
    #     parsed_feed = feedparser.parse(file_url, timeout=10)
    #     item = None
    #     for item in parsed_feed["items"]:
    #         print "item:", type(item)
    #         print "item:", item.keys()
    #         #break
    #     # Item has enclosure, so it should use that link
    #     #self.assertEquals(self.rssfeedhandler.get_link(item), item.enclosures[0]["href"])
    #     #del item["links"][:]
    #     # Item no longer has enclosures, so it should return the regular link
    #     #self.assertEquals(self.rssfeedhandler.get_link(item), item["link"])
    #
    # def test_test_get_rssfeed_parsed(self):
    #     #file_url = ""
    #     file_url = yarss2.util.common.get_resource("data/feeds/72020rarcategory_tv.xml", path="tests/")
    #     rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments",
    #                     "user_agent": None, "prefer_magnet": True}
    #     site_cookies = {"uid": "18463", "passkey": "b830f87d023037f9393749s932"}
    #     default_user_agent = self.rssfeedhandler.user_agent
    #     parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=site_cookies)
    #     print "parsed_feed:", parsed_feed.keys()
    #     #print "items:", parsed_feed["items"]
    #     for i in parsed_feed["items"]:
    #         print parsed_feed["items"][i]
    #         break

    # def test_download_link_with_equal_sign(self):
    #     file_url = yarss2.util.common.get_resource("rss_with_equal_sign_in_link.rss", path="tests/data/")
    #     from yarss2.lib.feedparser import feedparser
    #     from yarss2.torrent_handling import TorrentHandler, TorrentDownload
    #     rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments"}
    #     parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=None)
    #     print "parsed_feed:", parsed_feed["items"]


# Name:  FreeBSD-9.0-RELEASE-amd64-all
# Name:  FreeBSD-9.0-RELEASE-i386-all
# Name:  FreeBSD-9.0-RELEASE-ia64-all
# Name:  FreeBSD-9.0-RELEASE-powerpc-all
# Name:  FreeBSD-9.0-RELEASE-powerpc64-all
# Name:  FreeBSD-9.0-RELEASE-sparc64-all
# Name:  FreeBSD-9.0-RELEASE-amd64-bootonly
# Name:  FreeBSD-9.0-RELEASE-amd64-disc1
# Name:  FreeBSD-9.0-RELEASE-amd64-dvd1
# Name:  FreeBSD-9.0-RELEASE-amd64-memstick
# Name:  FreeBSD-9.0-RELEASE-i386-bootonly
# Name:  FreeBSD-9.0-RELEASE-i386-disc1
# Name:  FreeBSD-9.0-RELEASE-i386-dvd1
# Name:  FreeBSD-9.0-RELEASE-i386-memstick
# Name:  FreeBSD-9.0-RELEASE-ia64-bootonly
# Name:  FreeBSD-9.0-RELEASE-ia64-memstick
# Name:  FreeBSD-9.0-RELEASE-ia64-release
# Name:  FreeBSD-9.0-RELEASE-powerpc-bootonly
# Name:  FreeBSD-9.0-RELEASE-powerpc-memstick
# Name:  FreeBSD-9.0-RELEASE-powerpc-release
# Name:  FreeBSD-9.0-RELEASE-powerpc64-bootonly
# Name:  FreeBSD-9.0-RELEASE-powerpc64-memstick
# Name:  FreeBSD-9.0-RELEASE-powerpc64-release
# Name:  FreeBSD-9.0-RELEASE-sparc64-bootonly
# Name:  FreeBSD-9.0-RELEASE-sparc64-disc1
