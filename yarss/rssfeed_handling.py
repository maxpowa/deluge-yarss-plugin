#
# rssfeed_handling.py
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

import re
from deluge.log import LOG as log
from common import get_default_date
from lib import feedparser
from datetime import datetime 
from yarss.http import get_cookie_header

def get_rssfeed_parsed(rssfeed_data, cookies=None, cookie_header={}):

    return_dict = {}
    rssfeeds_dict = {}

    if cookies:
        cookie_header = get_cookie_header(cookies, rssfeed_data["site"])

    parsed_feeds = feedparser.parse(rssfeed_data["url"], request_headers=cookie_header)
    return_dict["raw_result"] = parsed_feeds

    log.info("YARSS: Fetching RSS Feed: '%s' with Cookie: '%s'." % (rssfeed_data["name"], cookie_header))

    # Error parsing
    if parsed_feeds["bozo"] == 1:
        log.warn("YARSS: Exception occured when fetching feed: %s" %
                 (str(parsed_feeds["bozo_exception"])))
        return_dict["bozo_exception"] = parsed_feeds["bozo_exception"]

    key = 0
    for item in parsed_feeds['items']:
        updated = item['updated_parsed']
        dt = datetime(* updated[:6])
        rssfeeds_dict[key] = {}
        rssfeeds_dict[key]["title"] = item['title']
        rssfeeds_dict[key]["link"] = item['link']
        rssfeeds_dict[key]["updated_datetime"] = dt
        rssfeeds_dict[key]["updated"] = dt.isoformat()
        rssfeeds_dict[key]["matches"] = False
        key += 1

    if key > 0:
        return_dict["items"] = rssfeeds_dict
    return return_dict

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
    p_include = p_exclude = None

    if options["regex_include"] is not None:
        flags = re.IGNORECASE if options["regex_include_ignorecase"] else 0
        p_include = re.compile(options["regex_include"], flags)

    if options["regex_exclude"] is not None and options["regex_exclude"] != "":
        flags = re.IGNORECASE if options["regex_exclude_ignorecase"] else 0
        p_exclude = re.compile(options["regex_exclude"], flags)

    for key in rssfeed_parsed.keys():
        item = rssfeed_parsed[key]
        title = item["title"]

        if item.has_key("regex_exclude_match"):
            del item["regex_exclude_match"]
        if item.has_key("regex_include_match"):
            del item["regex_include_match"]

        if p_include:
            m = p_include.search(title)
            if m:
                item["matches"] = True
                item["regex_include_match"] = m.span()
            else:
                item["matches"] = False
        if p_exclude:
            m = p_exclude.search(title)
            if m:
                item["matches"] = False
                item["regex_exclude_match"] = m.span()
        if item["matches"]:
            matching_items[key] = rssfeed_parsed[key]
    return matching_items


def fetch_subscription_torrents(config, rssfeed_key, subscription_key=None):
    """Called to fetch subscriptions from the rssfeed with key == rssfeed_key"""

    fetch_data = {}
    fetch_data["matching_torrents"] = []
    fetch_data["cookie_header"] = None
    fetch_data["rssfeed_items"] = None
    fetch_data["cookies_dict"] = config["cookies"]

    if rssfeed_key is None:
        if subscription_key is None:
            log.warn("rssfeed_key and subscription_key cannot both be None")
            return
        rssfeed_key = config["subscriptions"][subscription_key]["rssfeed_key"]

    rssfeed_data = config["rssfeeds"][rssfeed_key]
    log.info("YARSS: Update handler executed on RSS Feed %s (%s) upate interval %d." %
             (rssfeed_data["name"], rssfeed_data["site"], rssfeed_data["update_interval"]))

    for key in config["subscriptions"].keys():
        # subscription_key is given, only that subscription will be run
        if subscription_key and subscription_key != key:
            continue
        subscription_data = config["subscriptions"][key]
        if subscription_data["rssfeed_key"] == rssfeed_key and subscription_data["active"] == True:
            fetch_subscription(subscription_data, rssfeed_data, fetch_data)
    return fetch_data["matching_torrents"]

def fetch_subscription(subscription_data, rssfeed_data, fetch_data):
    """Search a feed with config 'subscription_data'"""
    log.info("YARSS: Fetching subscription '%s'." % subscription_data["name"])
    cookie_header = None

    if fetch_data["rssfeed_items"] is None:
        fetch_data["cookie_header"] = get_cookie_header(fetch_data["cookies_dict"], rssfeed_data["site"])
        rssfeed_parsed = get_rssfeed_parsed(rssfeed_data, cookie_header=fetch_data["cookie_header"])
        if rssfeed_parsed.has_key("bozo_exception"):
            log.warn("YARSS: bozo_exception when parsing rssfeed: %s" % str(rssfeed_parsed["bozo_exception"]))
        if rssfeed_parsed.has_key("items"):
            fetch_data["rssfeed_items"] = rssfeed_parsed["items"]
            if fetch_data["rssfeed_items"] is None:
                print "ERROR SETTING items to NONE"
        else:
            log.warn("YARSS: No items retrieved")
            return

    matches = update_rssfeeds_dict_matching(fetch_data["rssfeed_items"], options=subscription_data)

    try:
        newdate = datetime.strptime(subscription_data["last_update"], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        newdate = get_default_date()
    tmpdate = newdate

    #log.info("Matches: %d" % len(matches.keys()))

    # Sort by time?
    for key in matches.keys():
        if newdate < matches[key]["updated_datetime"]:
            log.info("YARSS: Adding torrent:" + (matches[key]["link"]))
            #add_torrent(matches[key]["link"], subscription_data)
            fetch_data["matching_torrents"].append((matches[key]["title"],
                                                    matches[key]["link"],
                                                    fetch_data["cookie_header"],
                                                    subscription_data))
            #subscription_data["last_update"] = matches[key]["updated_datetime"].isoformat()
        else:
            log.info("YARSS: Not adding, old timestamp:" + matches[key]["title"])
            del matches[key]

