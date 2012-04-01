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
from yarss2 import http

class HTTPTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_encode_cookie_values(self):
        expected = "key1=value1; key2=value2; key3=value3"
        cookie_pairs = []
        cookie_pairs.append(("key1", "value1"))
        cookie_pairs.append(("key2", "value2"))
        cookie_pairs.append(("key3", "value3"))
        encoded = http.encode_cookie_values(cookie_pairs)
        self.assertEquals(encoded, expected)

    def test_get_cookie_header(self):
        url = "http://basename.com/øashdnf/klasflas/dfnmalskdfn/malskdfnmasloal"
        cookies = {}
        cookies["0"] = {"active": True, "site": "basename.com", "value": [["key1", "value1"], ["key2", "value2"]]}
        cookies["1"] = {"active": True, "site": "non-matching-base-name.com", "value": [["key3", "value3"], ["key4", "value4"]]}
        cookies["2"] = {"active": False, "site": "basename.com", "value": [["key5", "value5"], ["key6", "value6"]]}
        expected_cookie = "key1=value1; key2=value2"
        header = http.get_cookie_header(cookies, url)

        self.assertTrue(header.has_key("Cookie"))
        self.assertEquals(header["Cookie"], expected_cookie)

    def test_url_fix(self):
        url = u"http://de.wikipedia.org/wiki/Elf (Begriffsklärung)"
        expected = "http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29"
        result = http.url_fix(url)
        self.assertEquals(expected, result)
