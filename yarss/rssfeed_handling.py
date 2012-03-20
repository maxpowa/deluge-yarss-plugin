#
# gtkui.py
#
# Copyright (C) 2012 Bro
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#       The Free Software Foundation, Inc.,
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA.
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

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

import feedparser
import datetime
import re


def get_cookie_header(cookies, url):
    matching_cookies = []
    for key in cookies_dict.keys():
        if not cookies[key]["active"]:
            continue
        # Test url match
        if url.find(cookies[key]["site"]) != -1:
            for key, value in cookies[key]["value"]:
                matching_cookies.append((key,value))

    if len(matching_cookies) == 0:
        return None
    return {"Cookie": encoded_values = encode_cookie_values(matching_cookies)}

def encode_cookie_values(values):
    """Takes a list of tuples containing key/value for a Cookie, 
    and returns the cookie as used in a HTTP Header"""
    cookie_value = ""
    for key, value in values:
        cookie_value += ("; %s=%s" % (key, value))
    return cookie_value[1:]

def get_rssfeed_parsed_dict(rssfeed_config, cookies_dict):

    rssfeeds_dict = {}

    header = get_cookie_header(cookies_dict, rssfeed_config["site"])

    parsed_feeds = feedparser.parse(self.rssfeed_config["url"])
    #parsed_feeds = feedparser.parse("/home/bro/test/RssServlet?digest=865ee613af273d32c5117080f13dc01f95bac1c0&hash=c3182bfdc067db100b3b518637be67439602de28")

    key = 0
    for item in parsed_feeds['items']:
        updated = item['updated_parsed']
        dt = datetime.datetime(* updated[:6])
        rssfeeds_dict[key] = {}
        rssfeeds_dict[key]["title"] = item['title']
        rssfeeds_dict[key]["link"] = item['link']
        rssfeeds_dict[key]["updated_datetime"] = dt
        rssfeeds_dict[key]["updated"] = dt.isoformat()
        rssfeeds_dict[key]["matches"] = False
        key += 1
    return rssfeeds_dict


def update_rssfeeds_dict_matching(rssfeed_parsed, options=None):
    """rssfeed_parsed: Dictionary returned by get_rssfeed_parsed_dict
    options, a dictionary with thw following keys:
    * "regex_include": str           
    * "regex_exclude": str          
    * "regex_include_ignorecase": bool
    * "regex_exclude_ignorecase": bool

    Updates the items in rssfeed_parsed
    Return: a dictionary of the matching items only.
    """
    matching_items = {}
    p_include = p_exclude =None

    if options["regex_include"] != None:
        flags = re.IGNORECASE if options["regex_include_ignorecase"] else 0
        p_include = re.compile(options["regex_include"], flags)

    if options["regex_exclude"] != None:
        flags = re.IGNORECASE if options["regex_exclude_ignorecase"] else 0
        p_exclude = re.compile(options["regex_exclude"], flags)
    
    for key in rssfeed_parsed.keys():
        item = rssfeed_parsed[key]
        title = item["title"]
        
        if p_include:
            m = p_include.search(title)
            if m:
                item["matches"] = True
                item["regex_include_match"] = m.span()
            else:
                item["matches"] = False
                if item.has_key("regex_include_match"):
                    del item["regex_include_match"]
        if p_exclude:
            m = p_exclude.search(title)
            if m:
                item["matches"] = False
                item["regex_exclude_match"] = m.span()
            else:
                if item.has_key("regex_exclude_match"):
                    del item["regex_exclude_match"]

        if item["matches"]:
            matching_items[key] = rssfeed_parsed[key]

    return matching_items
    

def fetch_subscription_torrents(config, rssfeed_key):
    
    rssfeed_data = config["rssfeeds"][rssfeed_key]
    log.info("YARSS: Update handler executed on RSS Feed %s (%s) upate interval %d." % 
             (rssfeed_data["name"], rssfeed_data["site"], rssfeed_data["update_interval"]))
    rss_cache = None
    for key in config["subscriptions"].keys():
        subscription_data = config["subscriptions"][key]
        if subscription_data["rssfeed_key"] == rssfeed_key and subscription_data["active"] == True:
            rss_cache = rssfeed_handling.fetch_subscription(subscription_data, rssfeed_data, 
                                                            config["cookies"], rss_cache)

def fetch_subscription(self, subscription_data, rssfeed_data, rss_cache, cookies):
    """Search a feed with config 'subscription_data'"""
    log.info("YARSS: Fetching subscription '%s'." % subscription_data["name"])
    if rss_cache == None:
        result_dict = get_rssfeed_parsed_dict(rssfeed_data, cookies)
    matches = update_rssfeeds_dict_matching(rssfeed_parsed, options=subscription_data)

    try:
        newdate = datetime.datetime.strptime(subscription_data["date"], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        newdate = get_default_date()
    tmpdate = newdate

    # Sort by time?
    for key in matches.keys():
        if newdate < matches[key]["updated_datetime"]:
            log.info("YARSS: Adding torrent:" + str(matches[key]["link"]))
            self.add_torrent(matches[key]["link"], subscription_data)
            subscription_data["date"] = matches[key]["updated_datetime"].isoformat()
        else:
            log.info("YARSS: Not adding, old timestamp:" + str(search_string))

    return rss_cache
