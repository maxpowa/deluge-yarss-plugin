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

import datetime
import threading

import twisted.internet.defer as defer
from twisted.trial import unittest

from deluge.config import Config
import deluge.configmanager
from deluge.log import LOG as log

import yarss2.util.common
import yarss2.yarss_config
from yarss2.rssfeed_handling import RSSFeedHandler

import common

class RSSFeedHandlingTestCase(unittest.TestCase):

    def setUp(self):
        self.log = log
        self.rssfeedhandler = RSSFeedHandler(self.log)

    def test_get_rssfeed_parsed(self):
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
        rssfeed_data = {"name": "Test", "url": file_url, "site:": "only used whith cookie arguments"}
        site_cookies = {"uid": "18463", "passkey": "b830f87d023037f9393749s932"}

        parsed_feed = self.rssfeedhandler.get_rssfeed_parsed(rssfeed_data, site_cookies_dict=site_cookies)

        # When needing to dump the result in json format
        #common.json_dump(parsed_feed["items"], "freebsd_rss_items_dump2.json")

        self.assertTrue(parsed_feed.has_key("items"))
        items = parsed_feed["items"]
        stored_items = common.load_json_testdata()
        self.assertTrue(yarss2.util.common.dicts_equals(items, stored_items, debug=False))
        self.assertEquals(parsed_feed["cookie_header"], {'Cookie': 'uid=18463; passkey=b830f87d023037f9393749s932'})

    def test_get_link(self):
        file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests/")
        from yarss2.lib.feedparser import feedparser
        parsed_feed = feedparser.parse(file_url)
        item = None
        for e in parsed_feed["items"]:
            item = e
            break
        # Item has enclosure, so it should use that link
        self.assertEquals(self.rssfeedhandler.get_link(item), item.enclosures[0]["href"])
        del item["links"][:]
        # Item no longer has enclosures, so it should return the regular link
        self.assertEquals(self.rssfeedhandler.get_link(item), item["link"])

    def test_get_size(self):
        file_url = yarss2.util.common.get_resource("t1.rss", path="tests/data/feeds/")
        from yarss2.lib.feedparser import feedparser
        parsed_feed = feedparser.parse(file_url)

        size = self.rssfeedhandler.get_size(parsed_feed["items"][0])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (4541927915.52, u'4.23 GB'))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][1])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (402349096.96, u'383.71 MB'))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][2])
        self.assertEquals(len(size), 1)
        self.assertEquals(size[0], (857007476))

        size = self.rssfeedhandler.get_size(parsed_feed["items"][3])
        self.assertEquals(len(size), 2)
        self.assertEquals(size[0], (14353107637))
        self.assertEquals(size[1], (13529146982.4, u'12.6 GB'))

    def get_default_rssfeeds_dict(self):
        match_option_dict = {}
        match_option_dict["regex_include"] = ""
        match_option_dict["regex_exclude"] = ""
        match_option_dict["regex_include_ignorecase"] = True
        match_option_dict["regex_exclude_ignorecase"] = True
        match_option_dict["custom_text_lines"] = None

        rssfeed_matching = {}
        rssfeed_matching["0"] = {"matches": False, "link": "", "title": "FreeBSD-9.0-RELEASE-amd64-all"}
        rssfeed_matching["1"] = {"matches": False, "link": "", "title": "FreeBSD-9.0-RELEASE-i386-all"}
        rssfeed_matching["2"] = {"matches": False, "link": "", "title": "fREEbsd-9.0-RELEASE-i386-all"}
        return match_option_dict, rssfeed_matching

    def test_update_rssfeeds_dict_matching(self):
        options, rssfeed_parsed = self.get_default_rssfeeds_dict()
        options["regex_include"] = "FreeBSD"
        matching, msg  = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()))

        # Also make sure the items in 'matching' correspond to the matching items in rssfeed_parsed
        count = 0
        for key in rssfeed_parsed.keys():
            if rssfeed_parsed[key]["matches"]:
                self.assertTrue(matching.has_key(key), "The matches dict does not contain the matching key '%s'" % key)
                count += 1
        self.assertEquals(count, len(matching.keys()),
                          "The number of items in matches dict (%d) does not match the number of matching items (%d)" % (count, len(matching.keys())))

        options["regex_include_ignorecase"] = False
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 1)

        #options["regex_include_ignorecase"] = True
        options["regex_exclude"] = "i386"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), len(rssfeed_parsed.keys()) - 2)

        # Fresh options
        options, rssfeed_parsed = self.get_default_rssfeeds_dict()

        # Custom line with unicode characters, norwegian ø and å, as well as Latin Small Letter Lambda with stroke
        options["custom_text_lines"] = [u"Test line with æ and å, as well as ƛ"]
        options["regex_include"] = "æ"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (15, 17))

        options["regex_include"] = "with.*ƛ"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        self.assertEquals(len(matching.keys()), 1)
        for key in matching.keys():
            self.assertEquals(matching[key]["title"], options["custom_text_lines"][0])
            self.assertEquals(matching[key]["regex_include_match"], (10, 39))

        # Test exclude span
        options["regex_include"] = ".*"
        options["regex_exclude"] = "line.*å"
        matching, msg = self.rssfeedhandler.update_rssfeeds_dict_matching(rssfeed_parsed, options)
        for key in rssfeed_parsed.keys():
            if not rssfeed_parsed[key]["matches"]:
                self.assertEquals(rssfeed_parsed[key]["title"], options["custom_text_lines"][0])
                self.assertEquals(rssfeed_parsed[key]["regex_exclude_match"], (5, 24))
                break

    def test_fetch_feed_torrents(self):
        config = get_test_config_dict()                                # 0 is the rssfeed key
        matche_result = self.rssfeedhandler.fetch_feed_torrents(config, "0")
        matches = matche_result["matching_torrents"]
        self.assertTrue(len(matches) == 3)

    #def test_label(self):
    #    #from deluge.ui.client import sclient
    #    #sclient.set_core_uri()
    #    #print sclient.get_enabled_plugins()
    #    import deluge.component as component
    #    from deluge.core.pluginmanager import PluginManager
    #    from deluge.ui.client import client
    #    plugins = PluginManager(self)
    #    # Enable plugins
    #    plugins.start()
    #
    #    print "Enabled   plugins:", plugins.get_enabled_plugins()
    #    print "Available plugins:", plugins.get_available_plugins()
    #    if "Label" in plugins.get_available_plugins():
    #        print "Label plugin found"
    #
    #    plugins.enable_plugin("Label")
    #
    #    print "info:", plugins.get_plugin_info("Label")
    #    print "Enabled   plugins:", plugins.get_enabled_plugins()
    #    #client.label.enable()
    #    #print "label:", client.label.get_labels()

####################################
## Helper methods for test data
####################################

def get_test_config_dict():
    config =  yarss2.yarss_config.default_prefs()
    file_url = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests")
    rssfeeds = common.get_default_rssfeeds(3)
    subscriptions = common.get_default_subscriptions(5)

    rssfeeds["0"]["name"] = "Test RSS Feed"
    rssfeeds["0"]["url"] = file_url
    rssfeeds["1"]["name"] = "Test RSS Feed2"
    rssfeeds["1"]["active"] = False

    subscriptions["0"]["name"] = "Matching subscription"
    subscriptions["0"]["regex_include"] = "sparc64"
    subscriptions["1"]["name"] = "Non-matching subscription"
    subscriptions["1"]["regex_include"] = None
    subscriptions["2"]["name"] = "Inactive subscription"
    subscriptions["2"]["active"] = False
    subscriptions["3"]["name"] = "Update_time too new"
    subscriptions["3"]["last_match"] = datetime.datetime.now().isoformat()
    subscriptions["4"]["name"] = "Wrong rsskey subscription"
    subscriptions["4"]["rssfeed_key"] = "1"

    config["rssfeeds"] = rssfeeds
    config["subscriptions"] = subscriptions
    return config

#Name:  FreeBSD-9.0-RELEASE-amd64-all
#Name:  FreeBSD-9.0-RELEASE-i386-all
#Name:  FreeBSD-9.0-RELEASE-ia64-all
#Name:  FreeBSD-9.0-RELEASE-powerpc-all
#Name:  FreeBSD-9.0-RELEASE-powerpc64-all
#Name:  FreeBSD-9.0-RELEASE-sparc64-all
#Name:  FreeBSD-9.0-RELEASE-amd64-bootonly
#Name:  FreeBSD-9.0-RELEASE-amd64-disc1
#Name:  FreeBSD-9.0-RELEASE-amd64-dvd1
#Name:  FreeBSD-9.0-RELEASE-amd64-memstick
#Name:  FreeBSD-9.0-RELEASE-i386-bootonly
#Name:  FreeBSD-9.0-RELEASE-i386-disc1
#Name:  FreeBSD-9.0-RELEASE-i386-dvd1
#Name:  FreeBSD-9.0-RELEASE-i386-memstick
#Name:  FreeBSD-9.0-RELEASE-ia64-bootonly
#Name:  FreeBSD-9.0-RELEASE-ia64-memstick
#Name:  FreeBSD-9.0-RELEASE-ia64-release
#Name:  FreeBSD-9.0-RELEASE-powerpc-bootonly
#Name:  FreeBSD-9.0-RELEASE-powerpc-memstick
#Name:  FreeBSD-9.0-RELEASE-powerpc-release
#Name:  FreeBSD-9.0-RELEASE-powerpc64-bootonly
#Name:  FreeBSD-9.0-RELEASE-powerpc64-memstick
#Name:  FreeBSD-9.0-RELEASE-powerpc64-release
#Name:  FreeBSD-9.0-RELEASE-sparc64-bootonly
#Name:  FreeBSD-9.0-RELEASE-sparc64-disc1




####################################
## Testing RSS Feed Timer
####################################

from deluge.log import LOG as log

from yarss2.rssfeed_handling import RSSFeedTimer
from common import get_default_rssfeeds

from test_torrent_handling import TestComponent

class RSSFeedTimerTestCase(unittest.TestCase):

    def setUp(self):
        self.rssfeeds = get_default_rssfeeds(5)
        self.rssfeeds["0"]["update_interval"] = 1
        self.rssfeeds["1"]["update_interval"] = 3
        self.rssfeeds["2"]["update_interval"] = 10
        self.rssfeeds["3"]["update_interval"] = 30
        self.rssfeeds["4"]["update_interval"] = 120

        self.config = common.get_test_config()
        self.config.set_config({"rssfeeds": self.rssfeeds, "email_configurations": {"send_email_on_torrent_events": False} })

        self.timer = RSSFeedTimer(self.config, log)
        test_component = TestComponent()
        self.timer.torrent_handler.download_torrent_file = test_component.download_torrent_file
        self.timer.enable_timers()

    def tearDown(self):
        # Must stop loopingcalls or test fails
        self.timer.disable_timers()

    def test_enable_timers(self):
        # Now verify the timers
        for key in self.timer.rssfeed_timers.keys():
            # Is the timer running?
            self.assertTrue(self.timer.rssfeed_timers[key]["timer"].running)

            # Does the timer have the correct interval?
            interval = self.timer.rssfeed_timers[key]["timer"].interval
            self.assertEquals(self.rssfeeds[key]["update_interval"] * 60, interval)
            self.assertEquals(self.rssfeeds[key]["update_interval"], self.timer.rssfeed_timers[key]["update_interval"])

    def test_disable_timers(self):
        self.timer.disable_timers()

        # Now verify that the timers have been stopped
        for key in self.timer.rssfeed_timers.keys():
            # Is the timer running?
            self.assertFalse(self.timer.rssfeed_timers[key]["timer"].running)

    def test_delete_timer(self):
        # Delete timer
        self.assertTrue(self.timer.delete_timer("0"))
        self.assertFalse(self.timer.delete_timer("-1"))

        self.assertEquals(len(self.timer.rssfeed_timers.keys()), 4)
        self.assertFalse(self.timer.rssfeed_timers.has_key("0"))

    def test_reschedule_timer(self):
        # Change interval to 60 minutes
        self.assertTrue(self.timer.set_timer("0", 60))

        interval = self.timer.rssfeed_timers["0"]["timer"].interval
        self.assertEquals(60 * 60, interval)
        self.assertEquals(self.timer.rssfeed_timers["0"]["update_interval"], 60)

    def test_schedule_timer(self):
        # Add new timer (with key "5") with interval 60 minutes
        self.assertTrue(self.timer.set_timer("5", 60))

        # Verify timer values
        interval = self.timer.rssfeed_timers["5"]["timer"].interval
        self.assertEquals(60 * 60, interval)
        self.assertEquals(self.timer.rssfeed_timers["5"]["update_interval"], 60)

        # Should now be 6 timers
        self.assertEquals(len(self.timer.rssfeed_timers.keys()), 6)

    def test_interval_unchanged(self):
        # Set timer 0 with same interval
        self.assertFalse(self.timer.set_timer("0", 1))

    def test_rssfeed_update_handler(self):
        subscription = yarss2.yarss_config.get_fresh_subscription_config(rssfeed_key="0", key="0")
        self.config.set_config({"subscriptions": {"0": subscription} })

        # Check that last_update changes
        old_last_update = self.rssfeeds["0"]["last_update"]

        # Run the rssfeed with key 0
        self.timer.rssfeed_update_handler("0")
        self.assertNotEquals(old_last_update, self.rssfeeds["0"]["last_update"])

        old_last_update = self.rssfeeds["0"]["last_update"]

        # Run the subscription with key 0 like when the user runs it manually
        self.timer.rssfeed_update_handler(None, "0")

        # last_update should not have changed
        self.assertEquals(old_last_update, self.rssfeeds["0"]["last_update"])


    def test_ttl_value_updated(self):
        config = get_test_config_dict()
        config["rssfeeds"]["0"]["update_interval"] = 30
        config["rssfeeds"]["0"]["obey_ttl"] = True
        config["rssfeeds"]["0"]["url"] = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests")

        yarss_config = common.get_test_config()
        yarss_config.set_config(config)

        self.timer.disable_timers()
        self.timer.yarss_config = yarss_config
        self.timer.enable_timers()

        def add_torrents_pass(*arg):
            pass
        self.timer.add_torrent_func = add_torrents_pass

        # Run the rssfeed with key 0
        self.timer.rssfeed_update_handler("0")

        # Verify that update_interval of rssfeed in config was updated
        self.assertEquals(yarss_config.get_config()["rssfeeds"]["0"]["update_interval"], 60)

        # Verify that update_interval of the timer was updated
        self.assertEquals(self.timer.rssfeed_timers["0"]["update_interval"], 60)
        self.timer.disable_timers()

    def test_rssfeed_update_queue(self):
        """Tests that the add_torrent_func is called the correct number of times,
        and that add_torrent_func is running in the main thread.
        """
        # Don't use the loopingcall, so disable just to avoid any trouble
        self.timer.disable_timers()
        self.config.set_config(get_test_config_dict())

        add_torrents_count = []
        main_thread = threading.current_thread()

        def add_torrents_cb(*arg):
            self.assertEquals(main_thread, threading.current_thread(), "add_torrents must be called from the main thread!")
            add_torrents_count.append(0)
        self.timer.add_torrent_func = add_torrents_cb

        d_first = self.timer.queue_rss_feed_update(rssfeed_key="0")
        self.timer.queue_rss_feed_update(subscription_key="1")
        self.timer.queue_rss_feed_update(rssfeed_key="1")
        d_last = self.timer.queue_rss_feed_update(rssfeed_key="2")

        def verify_callback_count(args):
            self.assertEquals(len(add_torrents_count), 4)

        d_verify_callback = defer.Deferred()
        d_verify_callback.addCallback(verify_callback_count)
        # Add verify_callback_results to the deferred chain
        d_last.chainDeferred(d_verify_callback)
        return d_first

    def test_task_queue(self):
        """Test the RSSFeedRunQueue
        Test that the jobs are not run in main thread and that the jobs are run sequentially
        """
        from twisted.internet import task
        from yarss2.rssfeed_handling import RSSFeedRunQueue

        main_thread = threading.current_thread()
        runtime_dict = {}
        def test_run(id):
            # Save the start and end time of the job
            runtime_dict[id] = {"start": yarss2.util.common.get_current_date()}
            # Test that the job is not run in main thread
            self.assertNotEquals(threading.current_thread(), main_thread)
            runtime_dict[id]["end"] = yarss2.util.common.get_current_date()
            return id

        result_callback_ids = []

        def result_callback(id):
            result_callback_ids.append(id)

        ids = [str(i) for i in range(10)]
        taskq = RSSFeedRunQueue()
        # Start id_count jobs
        for id in ids:
            d = taskq.push(test_run, str(id))
            d.addCallback(result_callback)

        def verify_times(arg):
            """Verify that start time is later than the previous job's end time"""
            tmp_date = yarss2.util.common.get_default_date()
            for id in range(len(ids)):
                runtime_dict[str(id)]
                self.assertTrue(tmp_date < runtime_dict[str(id)]["start"])
                tmp_date = runtime_dict[str(id)]["end"]
        d_verify = defer.Deferred()
        d_verify.addCallback(verify_times)
        # Add verify_times to the last added deferred
        d.chainDeferred(d_verify)

        def verify_callback_results(args):
            self.assertEquals(len(ids), len(result_callback_ids))
            for i in range(len(ids)):
                self.assertEquals(ids[i], result_callback_ids[i])

        d_verify_callback = defer.Deferred()
        d_verify_callback.addCallback(verify_callback_results)
        # Add verify_callback_results to the deferred chain
        d_verify.chainDeferred(d_verify_callback)
        return d_verify
