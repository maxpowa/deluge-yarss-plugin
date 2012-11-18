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
from yarss2.util import http
import yarss2.yarss_config
from yarss2.lib.feedparser import feedparser
from yarss2.util import common

class HTTPTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_encode_cookie_values(self):
        expected = "key3=value3; key2=value2; key1=value1"
        cookie_pairs = {}
        cookie_pairs["key1"] = "value1"
        cookie_pairs["key2"] = "value2"
        cookie_pairs["key3"] = "value3"
        encoded = http.encode_cookie_values(cookie_pairs)
        self.assertEquals(encoded, expected)

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
        self.assertEquals(header["Cookie"], expected_cookie)

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

