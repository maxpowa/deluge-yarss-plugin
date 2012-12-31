#
# rssfeed_scheduler.py
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

import twisted.internet.defer as defer
from twisted.internet.task import LoopingCall
from twisted.internet import threads
from twisted.python.failure import Failure

import deluge.component as component

from yarss2.yarss_config import YARSSConfigChangedEvent
from yarss2.torrent_handling import TorrentHandler
from yarss2.rssfeed_handling import RSSFeedHandler

class RSSFeedScheduler(object):
    """Handles scheduling the RSS Feed fetches."""

    def __init__(self, config, logger):
        self.yarss_config = config
        self.rssfeed_timers = {}
        self.run_queue = RSSFeedRunQueue()
        self.log = logger
        self.rssfeedhandler = RSSFeedHandler(logger)
        self.torrent_handler = TorrentHandler(logger)
        self.add_torrent_func = self.torrent_handler.add_torrents # To make it possible to disable adding torrents in testing

    def enable_timers(self):
        """Creates the LoopingCall timers, one for each RSS Feed"""
        config = self.yarss_config.get_config()
        for key in config["rssfeeds"]:
            self.set_timer(config["rssfeeds"][key]["key"], config["rssfeeds"][key]['update_interval'])
            self.log.info("Scheduled RSS Feed '%s' with interval %s" %
                     (config["rssfeeds"][key]["name"], config["rssfeeds"][key]["update_interval"]))

    def disable_timers(self):
        for key in self.rssfeed_timers.keys():
            self.rssfeed_timers[key]["timer"].stop()
            del self.rssfeed_timers[key]

    def set_timer(self, key, interval):
        """Schedule a timer for the specified interval."""
        try:
            interval = int(interval)
        except:
            self.log.error("Failed to convert interval '%s' to int!" % str(interval))
        # Already exists, so reschedule if interval has changed
        if self.rssfeed_timers.has_key(key):
            # Interval is the same, so return
            if self.rssfeed_timers[key]["update_interval"] == interval:
                return False
            self.rssfeed_timers[key]["timer"].stop()
            self.rssfeed_timers[key]["update_interval"] = interval
        else:
            # New timer
            # Second argument, the rssfeedkey is passed as argument in the callback method
            #timer = LoopingCall(self.rssfeed_update_handler, (key))
            timer = LoopingCall(self.queue_rssfeed_update, key)

            self.rssfeed_timers[key] = {"timer": timer, "update_interval": interval}
        self.rssfeed_timers[key]["timer"].start(interval * 60, now=False) # Multiply to get seconds
        return True

    def delete_timer(self, key):
        """Delete timer with the specified key."""
        if not self.rssfeed_timers.has_key(key):
            self.log.warn("Cannot delete timer. No timer with key %s" % key)
            return False
        self.rssfeed_timers[key]["timer"].stop()
        del self.rssfeed_timers[key]
        return True

    def rssfeed_update_handler(self, rssfeed_key=None, subscription_key=None):
        """Goes through all the feeds and runs the active ones.
        Multiple subscriptions on one RSS Feed will download the RSS feed page only once
        """
        if subscription_key:
            self.log.info("Manually running Subscription '%s'" %
                          (self.yarss_config.get_config()["subscriptions"][subscription_key]["name"]))
        elif rssfeed_key:
            if self.yarss_config.get_config()["rssfeeds"][rssfeed_key]["active"] is False:
                return
            #self.log.info("Running RSS Feed '%s'" % (self.yarss_config.get_config()["rssfeeds"][rssfeed_key]["name"]))
        fetch_result = self.rssfeedhandler.fetch_feed_torrents(self.yarss_config.get_config(), rssfeed_key,
                                                                       subscription_key=subscription_key)
        matching_torrents = fetch_result["matching_torrents"]
        # Fetching the torrent files. Do this slow task in non-main thread.
        for torrent in matching_torrents:
            torrent["torrent_download"] = self.torrent_handler.get_torrent(torrent)


        # Update TTL value?
        if fetch_result.has_key("ttl"):
            # Subscription is run directly. Get RSS Feed key
            if not rssfeed_key:
                rssfeed_key = self.yarss_config.get_config()["subscriptions"][subscription_key]["rssfeed_key"]
            self.log.info("Rescheduling RSS Feed '%s' with interval '%s' according to TTL." %
                     (self.yarss_config.get_config()["rssfeeds"][rssfeed_key]["name"], fetch_result["ttl"]))
            self.set_timer(rssfeed_key, fetch_result["ttl"])
            # Set new interval in config
            self.yarss_config.get_config()["rssfeeds"][rssfeed_key]["update_interval"] = fetch_result["ttl"]
        # Send YARSSConfigChangedEvent to GUI with updated config.
        try:
            # Tests throws KeyError for EventManager when running this method, so wrap this in try/except
            component.get("EventManager").emit(YARSSConfigChangedEvent(self.yarss_config.get_config()))
        except KeyError:
            pass

        def save_subscription_func(subscription_data):
            self.yarss_config.generic_save_config("subscriptions", data_dict=subscription_data)

        return (self.add_torrent_func, save_subscription_func,
                fetch_result["matching_torrents"], self.yarss_config.get_config())

    def add_torrents_callback(self, args):
        """This i called with the results from rssfeed_update_handler
        add_torrent_func must be called on the main thread
        """
        if args is None:
            return
        add_torrent_func, save_subscription_func, matching_torrents, config = args
        add_torrent_func(save_subscription_func, matching_torrents, config)

    def queue_rssfeed_update(self, *args, **kwargs):
        d = self.run_queue.push(self.rssfeed_update_handler, *args, **kwargs)
        d.addCallback(self.add_torrents_callback)
        return d


class RSSFeedRunQueue(object):
    """Runs functions in separate threads. If a job is already running,
    jobs pushed are queued until the running job has finished"""
    def __init__(self, concurrentMax=1):
        self.concurrentMax = concurrentMax
        self._running = 0
        self._queued = []

    def push(self, f, *args, **kwargs):
        """Push job to queue"""
        if self._running < self.concurrentMax:
            return self._run(f, args, kwargs)
        d = defer.Deferred()
        self._queued.append((f, args, kwargs, d))
        return d

    def _run(self, f, args, kwargs):
        """Run function in separate thread"""
        self._running += 1
        deferred = threads.deferToThread(f, *args, **kwargs)
        deferred.addBoth(self._try_queued)
        return deferred

    def _try_queued(self, r):
        """Execute next job in queue if it exists"""
        self._running -= 1
        if self._running < self.concurrentMax and self._queued:
            f, args, kwargs, d = self._queued.pop(0)
            new_d = self._run(f, args, kwargs)
            new_d.chainDeferred(d)
        if isinstance(r, Failure):
            r.trap()
        return r
