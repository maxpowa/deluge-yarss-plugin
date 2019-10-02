# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import re

PY2 = False
PY3 = False

try:
    import urllib.parse as urlparse
    from urllib.parse import quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus
    from html.parser import HTMLParser
    unicode = str
    PY3 = True
except ImportError as err:
    # python 2
    import urlparse
    from urllib import quote as urllib_quote
    from urllib import quote_plus as urllib_quote_plus
    from HTMLParser import HTMLParser
    PY2 = True


def download_file(url_file_stream_or_string, site_cookies_dict=None, etag=None, modified=None, user_agent=None,
                  referrer=None, handlers=None, request_headers=None, response_headers=None,
                  resolve_relative_uris=None, sanitize_html=None, timeout='Global'):
    from . import feedparsing
    result = dict(
        bozo = False,
        entries = [],
        feed = {},
        headers = {},
    )

    if site_cookies_dict:
        cookie_header = get_cookie_header(site_cookies_dict)
        if request_headers is None:
            request_headers = {}
        request_headers.update(cookie_header)
        print("request_headers:", request_headers)

    data = feedparsing._open_resource(url_file_stream_or_string, etag, modified, user_agent, referrer,
                                         handlers, request_headers, result, timeout=timeout)
    result['content'] = feedparsing.convert_to_utf8(result['headers'], data, result)
    return result


def get_matching_cookies_dict(cookies, url):
    """Takes a dictionary of cookie key/values, and
    returns a dict with the cookies matching the url
    """
    matching_cookies = {}
    if not cookies:
        return {}
    for key in cookies.keys():
        if not cookies[key]["active"]:
            continue
        # Test url match
        if url.find(cookies[key]["site"]) != -1:
            for k2 in cookies[key]["value"].keys():
                matching_cookies[k2] = cookies[key]["value"][k2]
    return matching_cookies


def get_cookie_header(cookies, url=None):
    """Takes a dictionary of cookie key/values,
    and returns the cookies matching url encoded
    as required in the HTTP request header."""
    if url:
        cookies = get_matching_cookies_dict(cookies, url)
    if len(cookies) == 0:
        return {}
    return {"Cookie": encode_cookie_values(cookies)}


def encode_cookie_values(cookies_dict):
    """Takes a dictionary of key/value for a Cookie,
    and returns the cookie as used in a HTTP Header"""
    cookie_value = ""
    for key in sorted(cookies_dict):
        cookie_value += ("; %s=%s" % (key, cookies_dict[key]))
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
    if PY2 and isinstance(s, unicode):
        s = s.encode(charset, 'ignore')

    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib_quote(path, safe="%/:=&?~#+!$,;'@()*[]")
    qs = urllib_quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


def clean_html_body(html_page):
    from bs4 import BeautifulSoup, Comment
    soup = BeautifulSoup(html_page, features="html5lib")
    comments = soup.findAll(text=lambda text: isinstance(html_page, Comment))
    [comment.extract() for comment in comments]

    # Removing head
    soup.html.head.extract()
    # Removing scripts
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('style')]

    for tag in soup():
        del tag["style"]

    s = HTMLStripper()
    s.feed(str(soup))
    safe_html = s.get_data()

    # Allow max two consecutive \n
    safe_html = re.sub(r'\n(\n)+', r'\n\n', safe_html)
    return safe_html


class HTMLStripper(HTMLParser):

    def __init__(self):
        super(HTMLStripper, self).__init__()
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


#from HTMLParser import HTMLParser
#
#class MLStripper(HTMLParser):
#
#    def __init__(self):
#        self.reset()
#        self.fed = []
#    def handle_data(self, d):
#        self.fed.append(d)
#    def get_data(self):
#        return ''.join(self.fed)