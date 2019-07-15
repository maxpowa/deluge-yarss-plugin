# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2019 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import sys

from twisted.trial import unittest
import pytest

from yarss2.util import http
import yarss2.yarss_config
from yarss2.util import common

from . import common as test_common


class HTTPTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        pass

    def test_encode_cookie_values(self):
        expected = ['key1=value1', 'key2=value2', 'key3=value3']
        cookie_pairs = {}
        cookie_pairs["key1"] = "value1"
        cookie_pairs["key2"] = "value2"
        cookie_pairs["key3"] = "value3"
        encoded = http.encode_cookie_values(cookie_pairs)
        self.assertEquals(sorted(encoded.split("; ")), expected)

    def test_get_cookie_header(self):
        url = "http://basename.com/øashdnf/klasflas/dfnmalskdfn/malskdfnmasloal"
        cookies = {}
        cookies["0"] = {"active": True, "site": "basename.com",
                        "value": {"key1": "value1", "key2": "value2"}}
        cookies["1"] = {"active": True, "site": "non-matching-base-name.com",
                        "value": {"key3": "value3", "key4": "value4"}}
        cookies["2"] = {"active": False, "site": "basename.com",
                        "value": {"key5": "value5", "key6": "value6"}}
        expected_cookie = "key2=value2; key1=value1"
        header = http.get_cookie_header(cookies, url)
        self.assertTrue("Cookie" in header)
        self.assertEquals(sorted(header["Cookie"].split("; ")), sorted(expected_cookie.split("; ")))

    def test_get_matching_cookies_dict(self):
        cookies = {}
        cookies["0"] = yarss2.yarss_config.get_fresh_cookie_config()
        cookies["0"]["site"] = "basename.com"
        cookies["0"]["value"]["key1"] = "value1"
        cookies["0"]["value"]["key2"] = "value2"
        cookies["1"] = yarss2.yarss_config.get_fresh_cookie_config()
        cookies["1"]["site"] = "non-matching_url.com"
        cookies["1"]["value"]["key3"] = "value3"

        matching_cookies = http.get_matching_cookies_dict(cookies, "http://basename.com/blabla")
        self.assertTrue("key1" in matching_cookies)
        self.assertEquals(matching_cookies["key1"], cookies["0"]["value"]["key1"])
        self.assertTrue("key2" in matching_cookies)
        self.assertEquals(matching_cookies["key2"], cookies["0"]["value"]["key2"])
        self.assertFalse("key3" in matching_cookies)

    def test_url_fix(self):
        url = u"http://de.wikipedia.org/wiki/Elf (Begriffsklärung)"
        expected = "http://de.wikipedia.org/wiki/Elf%20(Begriffskl%C3%A4rung)"
        result = http.url_fix(url)
        self.assertEquals(expected, result)

    @pytest.mark.skipif(sys.version_info[0] == 3, reason="python 2")
    def test_feedparser_ampersant_in_url(self):
        """A bug in feedparser resulted in URL containing &amp when XML Parser was not available.
        This test disables XML Parser and verifies that the URL is correct
        """
        from yarss2.lib import feedparser
        file_path = common.get_resource("rss_with_ampersand_link.rss", path="tests")
        # This is the link in rss_with_ampersand_link.rss
        expected = "http://hostname.com/Fetch?hash=2f21d4e59&digest=865178f9bc"
        # Disable XML Parser
        feedparser.feedparser._XML_AVAILABLE = 0
        parsed_feeds = feedparser.feedparser.parse(file_path)

        for item in parsed_feeds['items']:
            self.assertEquals(expected, item["link"])
            break

    def test_clean_html_body(self):
        from yarss2 import load_libs
        load_libs()
        web_page = """<html>
  <head>
   <title>
    Page title
   </title>
  </head>
  <body>
   <p id="firstpara" align="center">
    This is paragraph
    <b>
     one
    </b>
   </p>
   <p id="secondpara" align="blah">
    This is paragraph
    <b>
     two
    </b>
   </p>
  </body>
 </html>"""
        http.clean_html_body(web_page)

    def test_atoma_parsing(self):
        from yarss2.lib.atoma import atoma
        filename = "ettv-rss-1.xml"
        file_path = common.get_resource(filename, path="tests/data/feeds/")
        parsed_feeds = atoma.parse_rss_file(file_path)

        self.assertEquals('The top100 torrents', parsed_feeds.description)
        self.assertEquals('https://therss.so', parsed_feeds.link)
        self.assertEquals(None, parsed_feeds.ttl)

    @pytest.mark.skip()
    def test_rssfeed_handling_fetch_feedparser(self):
        """A bug in feedparser resulted in URL containing &amp when XML Parser was not available.
        This test disables XML Parser and verifies that the URL is correct
        """
        from yarss2 import rssfeed_handling
        filename = "ezrss-rss-full.xml"
        #filename = "ezrss-rss-full2.xml"
        filename = "ezrss-rss-3.xml"
        #filename = "freebsd_rss.xml"
        #filename = "ezrss-rss-4.xml"

        file_path = common.get_resource(filename, path="tests/data/feeds/")
        parsed_feeds = rssfeed_handling.fetch_and_parse_rssfeed(file_path)

        #print("parsed_feeds:", parsed_feeds)

        feed = parsed_feeds['feed']
        #print("\nfeed:", feed)

        entries = parsed_feeds['entries']
        #print("\nentries(%s): %s" % (len(entries), entries))
        print("\nentries(%s): %s" % (len(entries), ""))

        links = feed['links']
        print("\nlinks(%s): %s" % (len(links), links))

        #print("\nparsed_feeds - entries(%s): %s" % (len(parsed_feeds['entries']), parsed_feeds['entries']))
        entry1 = parsed_feeds['items'][0]
        print("entry 0:", entry1)
        #print("entry 0:", entry1.item)
        self.assertEquals('The.Other.Show.HDTV.x264-SVA[ettv]', entry1['title'])
        magnet_link = 'magnet:?xt=urn:btih:D62CA80E996599057B28DB63511F02610DEB6A8E&dn=The.Other.Show.HDTV.x264-SVA%5Bettv%5D'
        magnet_uri = magnet_link.replace('&', '&amp;')

        #self.assertEquals(magnet_link, entry1['links'][0]['href'])
        self.assertEquals(magnet_link, entry1['link'])
        self.assertEquals('336607878', entry1['contentlength'])
        self.assertEquals('D62CA80E996599057B28DB63511F02610DEB6A8E', entry1['infohash'])
        self.assertEquals(magnet_uri, entry1['magneturi'])
        self.assertEquals('', entry1['torrent'])
