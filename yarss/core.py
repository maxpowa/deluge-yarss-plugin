#
# core.py
#
# Copyright (C) 2009 Camillo Dell'mour <cdellmour@gmail.com>
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
from deluge._libtorrent import lt
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import re
from twisted.internet.task import LoopingCall

import rssfeed_handling

from yarss_config import YARSSConfig

from common import *

class Core(CorePluginBase):

    def enable(self):
        self.yarss_config = YARSSConfig()
        self.config = self.yarss_config.get_config()
        #self.update_status_timer = LoopingCall(self.update_handler)
        #self.update_status_timer.start(self.config['updatetime'] * 60) # Multiply to get seconds
        self.setup_timers()

    def disable(self):
        for key in self.rssfeed_timers.keys():
            self.rssfeed_timers[key].stop()
        self.yarss_config.save()

    def update(self):
        pass

    def setup_timers(self):
        """Creates the LoopingCall timers, one for each RSS Feed"""
        self.rssfeed_timers = {}
        for key in self.config["rssfeeds"]:
            timer = LoopingCall(self.rssfeed_update_handler, (self.config["rssfeeds"][key]["key"]))
            self.rssfeed_timers[key] = timer
            timer.start(self.config["rssfeeds"][key]['update_interval'] * 60, now=False) # Multiply to get seconds
            log.info("YARSS: Starting timer for RSS Feed '%s' with interval %d minutes." % 
                     (self.config["rssfeeds"][key]['name'],
                      self.config["rssfeeds"][key]['update_interval']))

    def rssfeed_update_handler(self, rssfeed_key):
        """Goes through all the feeds and runs the active ones.
        Multiple subscriptions on one RSS Feed will download the RSS only once"""
        rssfeed_handling.fetch_subscription_torrents(self.yarss_config.config, rssfeed_key)

    @export
    def set_config(self, config):
        self.yarss_config.set_config(config)

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.yarss_config.get_config()

    @export
    def refresh(self,updatetime = 0):
        """Not Used?"""
        self.update_status_timer.stop()
        if updatetime == 0:
            self.update_status_timer.start(self.config['updatetime'])
        else:
            self.update_status_timer.start(updatetime)

    @export
    def run_feed_test(self):
        """Runs the update handler"""
        log.info("YARSS: Running feed test")
        self.rssfeed_update_handler()


    @export
    def save_subscription(self, dict_key=None, subscription_data=None, delete=False):
        try:
            return self.yarss_config.generic_save_config("subscriptions", dict_key=dict_key, 
                                                         data_dict=subscription_data, delete=delete)
        except ValueError as (v):
            log.error("save_subscription: Failed to save subscription:" + str(v))

    @export
    def save_rssfeed(self, dict_key=None, rssfeed_data=None, delete=False):
        try:
            return self.yarss_config.generic_save_config("rssfeeds", dict_key=dict_key, 
                                                         data_dict=rssfeed_data, delete=delete)
        except ValueError as (v):
            log.error("save_rssfeed: Failed to save rssfeed:" + str(v))

    @export
    def save_cookie(self, dict_key=None, cookie_data=None, delete=False):
        """Save cookie to config. If dict_key is None, create new key
        If cookie_dict is None, delete cookie with key==dict_key"""
        try:
            return self.yarss_config.generic_save_config("cookies", dict_key=dict_key, data_dict=cookie_data, delete=delete)
        except ValueError as (v):
            log.error("save_cookie: Failed to save cookie:" + str(v))

    @export
    def save_email_message(self, dict_key=None, message_data=None, delete=False):
        """Save email message to config. If dict_key is None, create new key
        If message_dict is None, delete message with key==dict_key"""
        try:
            return self.yarss_config.generic_save_config("email_messages", dict_key=dict_key, data_dict=message_data, delete=delete)
        except ValueError as (v):
            log.error("save_email_message: Failed to save email message:" + str(v))

