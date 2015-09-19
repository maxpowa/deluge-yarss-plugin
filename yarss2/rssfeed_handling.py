# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import datetime
import re

from yarss2.lib.feedparser import feedparser
from yarss2.util import common, http
from yarss2.yarss_config import get_default_user_agent


class RSSFeedHandler(object):

    def __init__(self, log):
        self.log = log
        self.user_agent = get_default_user_agent()

    def get_link(self, item):
        link = None
        if "link" in item:
            link = item['link']
            if len(item.enclosures) > 0 and "href" in item.enclosures[0]:
                link = item.enclosures[0]["href"]
        return link

    def _parse_size(self, string):
        size_bytes = 0
        size_str = None
        exp = re.compile("Size:\s*(?P<size>\d+(\.\d+)?)\s?(?P<unit>GB|MB)")
        match = exp.search(string)
        if match:
            groupdict = match.groupdict()
            size = groupdict["size"]
            unit = groupdict["unit"]
            size_str = "%s %s" % (size, unit)

            if unit == "GB":
                size_bytes = float(size) * 1024 * 1024 * 1024
            elif unit == "MB":
                size_bytes = float(size) * 1024 * 1024
        return size_bytes, size_str

    def get_size(self, item):
        size = []
        if len(item.enclosures) > 0 and "length" in item.enclosures[0]:
            s = item.enclosures[0]["length"]
            size.append(int(s))

        if "contentlength" in item:
            size_bytes = int(item["contentlength"])
            size.append(int(size_bytes))

        if "summary_detail" in item:
            val = item["summary_detail"]["value"]
            size_bytes, size_str = self._parse_size(val)
            if size_str and size_bytes:
                size.append((size_bytes, size_str))
        return size

    def get_rssfeed_parsed(self, rssfeed_data, site_cookies_dict=None):
        """
        rssfeed_data: A dictionary containing rss feed data as stored in the YaRSS2 config.
        site_cookies_dict: A dictionary of cookie values to be used for this rssfeed.
        """
        return_dict = {}
        rssfeeds_dict = {}
        cookie_header = {}
        user_agent = self.user_agent if not rssfeed_data["user_agent"] else rssfeed_data["user_agent"]
        return_dict["user_agent"] = user_agent

        if site_cookies_dict:
            cookie_header = http.get_cookie_header(site_cookies_dict)
            return_dict["cookie_header"] = cookie_header

        self.log.info("Fetching RSS Feed: '%s' with Cookie: '%s' and User-agent: '%s'." %
                      (rssfeed_data["name"], http.get_cookie_header(cookie_header), user_agent))

        # Will abort after 10 seconds if server doesn't answer
        try:
            parsed_feed = feedparser.parse(rssfeed_data["url"], request_headers=cookie_header,
                                           agent=user_agent, timeout=10)
        except Exception, e:
            self.log.warn("Exception occured in feedparser: " + str(e))
            self.log.warn("Feedparser was called with url: '%s' using cookies: '%s' and User-agent: '%s'" %
                          (rssfeed_data["url"], http.get_cookie_header(cookie_header), user_agent))
            self.log.warn("Stacktrace:\n" + common.get_exception_string())
            return None
        return_dict["raw_result"] = parsed_feed

        # Error parsing
        if parsed_feed["bozo"] == 1:
            return_dict["bozo_exception"] = parsed_feed["bozo_exception"]

        # Store ttl value if present
        if "ttl" in parsed_feed["feed"]:
            return_dict["ttl"] = parsed_feed["feed"]["ttl"]
        key = 0
        no_publish_time = False
        for item in parsed_feed['items']:
            # Some RSS feeds do not have a proper timestamp
            dt = None
            if 'published_parsed' in item:
                published = item['published_parsed']
                dt = datetime.datetime(* published[:6])
            else:
                no_publish_time = True
                return_dict["warning"] = "Published time not available!"

            # Find the link
            link = self.get_link(item)
            rssfeeds_dict[key] = self._new_rssfeeds_dict_item(item['title'], link=link, published_datetime=dt)
            key += 1
        if no_publish_time:
            self.log.warn("Published time is not available!")
        if key > 0:
            return_dict["items"] = rssfeeds_dict
        return return_dict

    def _new_rssfeeds_dict_item(self, title, link=None, published_datetime=None, key=None):
        d = {}
        d["title"] = title
        d["link"] = link
        d["updated_datetime"] = published_datetime
        d["matches"] = False
        d["updated"] = ""
        if published_datetime:
            d["updated"] = published_datetime.isoformat()
        if key is not None:
            d["key"] = key
        return d

    def update_rssfeeds_dict_matching(self, rssfeed_parsed, options):
        """rssfeed_parsed: Dictionary returned by get_rssfeed_parsed_dict
        options, a dictionary with the following keys:
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

        if "custom_text_lines" in options and options["custom_text_lines"]:
            if not type(options["custom_text_lines"]) is list:
                self.log.warn("type of custom_text_lines' must be list")
            else:
                for l in options["custom_text_lines"]:
                    key = common.get_new_dict_key(rssfeed_parsed, string_key=False)
                    rssfeed_parsed[key] = self._new_rssfeeds_dict_item(l, key=key)

        if options["regex_include"] is not None and options["regex_include"] != "":
            flags = re.IGNORECASE if options["regex_include_ignorecase"] else 0
            try:
                regex = common.string_to_unicode(options["regex_include"]).encode("utf-8")
                p_include = re.compile(regex, flags)
            except Exception, e:
                self.log.warn("Regex compile error:" + str(e))
                message = "Regex: %s" % e
                p_include = None

        if options["regex_exclude"] is not None and options["regex_exclude"] != "":
            flags = re.IGNORECASE if options["regex_exclude_ignorecase"] else 0
            try:
                regex = common.string_to_unicode(options["regex_exclude"]).encode("utf-8")
                p_exclude = re.compile(regex, flags)
            except Exception, e:
                self.log.warn("Regex compile error:" + str(e))
                message = "Regex: %s" % e
                p_exclude = None

        for key in rssfeed_parsed.keys():
            item = rssfeed_parsed[key]
            title = item["title"].encode("utf-8")

            if "regex_exclude_match" in item:
                del item["regex_exclude_match"]
            if "regex_include_match" in item:
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

    def fetch_feed_torrents(self, config, rssfeed_key, subscription_key=None):
        """Called to fetch torrents for a feed
        If rssfeed_key is not None, all subscriptions linked to that RSS Feed
        will be run.
        If rssfeed_key is None, only the subscription with key == subscription_key
        will be run
        """
        fetch_data = {}
        fetch_data["matching_torrents"] = []
        fetch_data["rssfeed_items"] = None

        if rssfeed_key is None:
            if subscription_key is None:
                self.log.warn("rssfeed_key and subscription_key cannot both be None")
                return fetch_data
            rssfeed_key = config["subscriptions"][subscription_key]["rssfeed_key"]
        else:
            # RSS Feed is not enabled
            if config["rssfeeds"][rssfeed_key]["active"] is False:
                return fetch_data

        rssfeed_data = config["rssfeeds"][rssfeed_key]
        fetch_data["site_cookies_dict"] = http.get_matching_cookies_dict(config["cookies"], rssfeed_data["site"])
        self.log.info("Update handler executed on RSS Feed '%s (%s)' (Update interval %d min)" %
                      (rssfeed_data["name"], rssfeed_data["site"], rssfeed_data["update_interval"]))

        for key in config["subscriptions"].keys():
            # subscription_key is given, only that subscription will be run
            if subscription_key is not None and subscription_key != key:
                continue
            subscription_data = config["subscriptions"][key]
            if subscription_data["rssfeed_key"] == rssfeed_key and subscription_data["active"] is True:
                self.fetch_feed(subscription_data, rssfeed_data, fetch_data)

        if subscription_key is None:
            # Update last_update value of the rssfeed only when rssfeed is run by the timer,
            # not when a subscription is run manually by the user.
            # Don't need microseconds. Remove because it requires changes to the GUI to not display them
            dt = common.get_current_date().replace(microsecond=0)
            rssfeed_data["last_update"] = dt.isoformat()
        return fetch_data

    def handle_ttl(self, rssfeed_data, rssfeed_parsed, fetch_data):
        if rssfeed_data["obey_ttl"] is False:
            return
        if "ttl" in rssfeed_parsed:
            # Value is already TTL, so ignore
            try:
                ttl = int(rssfeed_parsed["ttl"])
                if rssfeed_data["update_interval"] == ttl:
                    return
                # Verify that the TTL value is actually an integer (just in case)
                # At least 1 minute, and not more than one year
                if ttl > 0 and ttl < 524160:
                    fetch_data["ttl"] = ttl
                else:
                    self.log.warn("TTL value is invalid: %d" % ttl)
            except ValueError:
                self.log.warn("Failed to convert TTL value '%s' to int!" % rssfeed_parsed["ttl"])
        else:
            self.log.warn("RSS Feed '%s' should obey TTL, but feed has no TTL value." %
                          rssfeed_data["name"])
            self.log.info("Obey TTL option set to False")
            rssfeed_data["obey_ttl"] = False

    def fetch_feed(self, subscription_data, rssfeed_data, fetch_data):
        """Search a feed with config 'subscription_data'"""
        self.log.info("Fetching subscription '%s'." % subscription_data["name"])

        # Feed has not yet been fetched.
        if fetch_data["rssfeed_items"] is None:
            rssfeed_parsed = self.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=fetch_data["site_cookies_dict"])
            if rssfeed_parsed is None:
                return
            if "bozo_exception" in rssfeed_parsed:
                self.log.warn("bozo_exception when parsing rssfeed: %s" % str(rssfeed_parsed["bozo_exception"]))
            if "items" in rssfeed_parsed:
                fetch_data["rssfeed_items"] = rssfeed_parsed["items"]
                self.handle_ttl(rssfeed_data, rssfeed_parsed, fetch_data)
            else:
                self.log.warn("No items retrieved")
                return
        # Remove the custom text lines before matching (not strictly necessary though,
        # but they are only for testing in the DialogSubscription)
        options = subscription_data.copy()
        del options["custom_text_lines"]
        matches, message = self.update_rssfeeds_dict_matching(fetch_data["rssfeed_items"], options=options)
        self.log.info("%d items in feed, %d matches the filter." %
                      (len(fetch_data["rssfeed_items"]), len(matches.keys())))

        last_match_dt = common.isodate_to_datetime(subscription_data["last_match"])

        for key in matches.keys():
            # Discard match only if timestamp is available,
            # and the timestamp is older or equal to the last matching timestamp
            if matches[key]["updated_datetime"] and last_match_dt >= matches[key]["updated_datetime"]:
                if subscription_data["ignore_timestamp"] is True:
                    self.log.info("Old timestamp: '%s', but ignore option is enabled so add torrent anyways."
                                  % matches[key]["title"])
                else:
                    self.log.info("Not adding because of old timestamp: '%s'" % matches[key]["title"])
                    del matches[key]
                    continue
            fetch_data["matching_torrents"].append({"title": matches[key]["title"],
                                                    "link": matches[key]["link"],
                                                    "updated_datetime": matches[key]["updated_datetime"],
                                                    "site_cookies_dict": fetch_data["site_cookies_dict"],
                                                    "user_agent": rssfeed_data["user_agent"],
                                                    "subscription_data": subscription_data})
