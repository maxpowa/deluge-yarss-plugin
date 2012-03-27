# -*- coding: utf-8 -*-
#
# http.py
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

import urlparse
import urllib
from HTMLParser import HTMLParser

def get_cookie_header(cookies, url):
    matching_cookies = []
    if not cookies:
        return {}
    for key in cookies.keys():
        if not cookies[key]["active"]:
            continue
        # Test url match
        if url.find(cookies[key]["site"]) != -1:
            for key, value in cookies[key]["value"]:
                matching_cookies.append((key,value))
    if len(matching_cookies) == 0:
        return {}
    return {"Cookie": encode_cookie_values(matching_cookies)}

def encode_cookie_values(key_value_pairs):
    """Takes a list of tuples containing key/value for a Cookie,
    and returns the cookie as used in a HTTP Header"""
    cookie_value = ""
    for key, value in key_value_pairs:
        cookie_value += ("; %s=%s" % (key, value))
    return cookie_value[2:]

def url_fix(s, charset='utf-8'):
    """Taken from werkzeug.utils. Liecense: BSD"""

    """Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    >>> url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    :param charset: The target charset for the URL if the url was
                    given as unicode string.
    """
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))

class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        prev_empty = False
        data = ""
        for i in self.fed:
            empty = i.strip() == ""
            if empty and prev_empty:
                continue
            elif empty:
                data += "\n"
            else:
                data += i.rstrip()
            prev_empty = empty
        return data
    
