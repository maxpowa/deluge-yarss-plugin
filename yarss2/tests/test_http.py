# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest
from yarss2.util import http
import yarss2.yarss_config
from yarss2.lib.feedparser import feedparser
from yarss2.util import common

class HTTPTestCase(unittest.TestCase):

    def setUp(self):
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
        cookies["0"] = {"active": True,  "site": "basename.com",
                        "value": {"key1": "value1", "key2": "value2"}}
        cookies["1"] = {"active": True,  "site": "non-matching-base-name.com",
                        "value": {"key3": "value3", "key4": "value4"}}
        cookies["2"] = {"active": False, "site": "basename.com",
                        "value": {"key5": "value5", "key6": "value6"}}
        expected_cookie = "key2=value2; key1=value1"
        header = http.get_cookie_header(cookies, url)
        self.assertTrue(header.has_key("Cookie"))
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
        self.assertTrue(matching_cookies.has_key("key1"))
        self.assertEquals(matching_cookies["key1"], cookies["0"]["value"]["key1"])
        self.assertTrue(matching_cookies.has_key("key2"))
        self.assertEquals(matching_cookies["key2"], cookies["0"]["value"]["key2"])
        self.assertFalse(matching_cookies.has_key("key3"))

    def test_url_fix(self):
        url = u"http://de.wikipedia.org/wiki/Elf (Begriffsklärung)"
        expected = "http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29"
        result = http.url_fix(url)
        self.assertEquals(expected, result)

    def test_feedparser_ampersant_in_url(self):
        """A bug in feedparser resulted in URL containing &amp when XML Parser was not available.
        This test disables XML Parser and verifies that the URL is correct
        """
        file_path = common.get_resource("rss_with_ampersand_link.rss", path="tests")
        # This is the link in rss_with_ampersand_link.rss
        url = "http://hostname.com/Fetch?hash=2f21d4e59&amp;digest=865178f9bc"
        expected = "http://hostname.com/Fetch?hash=2f21d4e59&digest=865178f9bc"
        # Disable XML Parser
        feedparser._XML_AVAILABLE = 0
        parsed_feeds = feedparser.parse(file_path)

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
        cleaned = http.clean_html_body(web_page)

