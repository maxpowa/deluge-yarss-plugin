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
import traceback
from deluge.log import LOG as log
from common import isodate_to_datetime, string_to_unicode, get_new_dict_key
from lib import feedparser
from datetime import datetime 
from yarss2.http import get_cookie_header

def get_rssfeed_parsed(rssfeed_data, cookies=None, cookie_header={}):
    """
    rssfeed_data: A dictionary containing rss feed data as stored in the YaRSS2 config.
    cookies: A dictionary of cookie values as stored in the YaRSS2 config. cookie_header paramamer will not be used
    cookie_header: A dictionary of cookie values as returned by yarss2.http.get_cookie_header.
    """
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
        rssfeeds_dict[str(key)] = new_rssfeeds_dict_item(item['title'], item['link'], dt)
        key += 1

    if key > 0:
        return_dict["items"] = rssfeeds_dict
    return return_dict

def new_rssfeeds_dict_item(title, link=None, updated_datetime=None, key=None):
    d = {}
    d["title"] = title
    d["link"] = link
    d["updated_datetime"] = updated_datetime
    d["matches"] = False
    d["updated"] = ""
    if updated_datetime:
        d["updated"] = updated_datetime.isoformat()
    if key is not None:
        d["key"] = key
    return d

def update_rssfeeds_dict_matching(rssfeed_parsed, options):
    """rssfeed_parsed: Dictionary returned by get_rssfeed_parsed_dict
    options, a dictionary with thw following keys:
    * "regex_include": str
    * "regex_exclude": str
    * "regex_include_ignorecase": bool
    * "regex_exclude_ignorecase": bool

    Updates the items in rssfeed_parsed
    Return: a dictionary of the matching items only.
    """
    # regex and title are converted from utf-8 unicode to ascii strings before matching
    # This is because the indexes returned by span must be the byte index of the text, 
    # because Pango attributes takes the byte index, and not character index.

    matching_items = {}
    p_include = p_exclude = None
    message = None

    # Remove old custom lines
    for key in rssfeed_parsed.keys():
        if rssfeed_parsed[key]["link"] is None:
            del rssfeed_parsed[key]

    if options.has_key("custom_text_lines") and options["custom_text_lines"]:
        if not type(options["custom_text_lines"]) is list:
            log.warn("YARSS: type of custom_text_lines' must be list")
        else:
            for l in options["custom_text_lines"]:
                key = get_new_dict_key(rssfeed_parsed, string_key=False)
                rssfeed_parsed[key] = new_rssfeeds_dict_item(l, key=key)

    if options["regex_include"] is not None:
        flags = re.IGNORECASE if options["regex_include_ignorecase"] else 0
        try:
            regex = string_to_unicode(options["regex_include"])
            regex = regex.encode("utf-8")
            p_include = re.compile(regex, flags)
        except Exception, e:
            traceback.print_exc(e)
            log.warn("YARSS: Regex compile error:" + str(e))
            message = e
            p_include = None

    if options["regex_exclude"] is not None and options["regex_exclude"] != "":
        flags = re.IGNORECASE if options["regex_exclude_ignorecase"] else 0
        try:
            regex = string_to_unicode(options["regex_exclude"])
            regex = regex.encode("utf-8")
            p_exclude = re.compile(regex, flags)
        except Exception, e:
            traceback.print_exc(e)
            log.warn("YARSS: Regex compile error:" + str(e))
            message = e
            p_exclude = None

    for key in rssfeed_parsed.keys():
        item = rssfeed_parsed[key]
        title = item["title"]
        title = title.encode("utf-8")

        if item.has_key("regex_exclude_match"):
            del item["regex_exclude_match"]
        if item.has_key("regex_include_match"):
            del item["regex_include_match"]

        item["matches"] = False
        if p_include:
            m = p_include.search(title)
            if m:
                item["matches"] = True
                item["regex_include_match"] = m.span()
        if p_exclude:
            m = p_exclude.search(title)
            if m:
                item["matches"] = False
                item["regex_exclude_match"] = m.span()
        if item["matches"]:
            matching_items[key] = rssfeed_parsed[key]
    return matching_items, message


def fetch_subscription_torrents(config, rssfeed_key, subscription_key=None):
    """Called to fetch subscriptions 
    If rssfeed_key is not None, all subscriptions linked to that RSS Feed 
    will be run.
    If rssfeed_key is None, only the subscription with key == subscription_key
    will be run
    """

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
    else:
        # RSS Feed is not enabled
        if config["rssfeeds"][rssfeed_key]["active"] is False:
            return fetch_data["matching_torrents"]

    rssfeed_data = config["rssfeeds"][rssfeed_key]
    log.info("YARSS: Update handler executed on RSS Feed %s (%s) upate interval %d." %
             (rssfeed_data["name"], rssfeed_data["site"], rssfeed_data["update_interval"]))

    for key in config["subscriptions"].keys():
        # subscription_key is given, only that subscription will be run
        if subscription_key is not None and subscription_key != key:
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
        else:
            log.warn("YARSS: No items retrieved")
            return

    matches, message = update_rssfeeds_dict_matching(fetch_data["rssfeed_items"], options=subscription_data)

    last_update_dt = isodate_to_datetime(subscription_data["last_update"])

    # Sort by time?
    for key in matches.keys():
        if last_update_dt < matches[key]["updated_datetime"]:
            log.info("YARSS: Adding torrent:" + (matches[key]["link"]))
            fetch_data["matching_torrents"].append({"title": matches[key]["title"],
                                                    "link": matches[key]["link"],
                                                    "updated_datetime": matches[key]["updated_datetime"],
                                                    "cookie_header": fetch_data["cookie_header"],
                                                    "subscription_data": subscription_data})
        else:
            log.info("YARSS: Not adding, old timestamp:" + matches[key]["title"])
            del matches[key]

