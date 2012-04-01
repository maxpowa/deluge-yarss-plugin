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

from twisted.internet.task import LoopingCall

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
from deluge.core.rpcserver import export

from yarss2.yarss_config import YARSSConfig
from yarss2.common import get_resource 
from yarss2.http import get_cookie_header
from yarss2 import torrent_handling
from yarss2 import rssfeed_handling

class Core(CorePluginBase):

    def enable(self):
        self.yarss_config = YARSSConfig()
        self.setup_timers()

    def disable(self):
        self.yarss_config.save()
        for key in self.rssfeed_timers.keys():
            self.rssfeed_timers[key].stop()

    def update(self):
        pass

    def setup_timers(self):
        """Creates the LoopingCall timers, one for each RSS Feed"""
        self.rssfeed_timers = {}
        config = self.yarss_config.get_config()
        for key in config["rssfeeds"]:
            timer = LoopingCall(self.rssfeed_update_handler, (config["rssfeeds"][key]["key"]))
            self.rssfeed_timers[key] = timer
            timer.start(config["rssfeeds"][key]['update_interval'] * 60, now=False) # Multiply to get seconds
            log.info("YARSS: Starting timer for RSS Feed '%s' with interval %d minutes." % 
                     (config["rssfeeds"][key]['name'],
                      config["rssfeeds"][key]['update_interval']))

    @export
    def rssfeed_update_handler(self, rssfeed_key, subscription_key=None):
        """Goes through all the feeds and runs the active ones.
        Multiple subscriptions on one RSS Feed will download the RSS only once"""
        matching_torrents = rssfeed_handling.fetch_subscription_torrents(self.yarss_config.get_config(), 
                                                                         rssfeed_key, 
                                                                         subscription_key=subscription_key)
        torrent_handling.add_torrents(self, matching_torrents, self.yarss_config.get_config())

    @export
    def set_config(self, config):
        self.yarss_config.set_config(config)

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.yarss_config.get_config()

    @export
    def save_email_configurations(self, email_configurations):
        conf = {"email_configurations": email_configurations}
        try:
            self.yarss_config.set_config(conf)
        except ValueError as (v):
            log.error("save_email_configurations: Failed to save email configurations:" + str(v))

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
            return self.yarss_config.generic_save_config("cookies", 
                                                         dict_key=dict_key, 
                                                         data_dict=cookie_data, 
                                                         delete=delete)
        except ValueError as (v):
            log.error("save_cookie: Failed to save cookie:" + str(v))

    @export
    def save_email_message(self, dict_key=None, message_data=None, delete=False):
        """Save email message to config. If dict_key is None, create new key
        If message_dict is None, delete message with key==dict_key"""
        try:
            return self.yarss_config.generic_save_config("email_messages", 
                                                         dict_key=dict_key, 
                                                         data_dict=message_data, 
                                                         delete=delete)
        except ValueError as (v):
            log.error("save_email_message: Failed to save email message:" + str(v))

    @export
    def add_torrent(self, torrent_url):
        cookie_header = get_cookie_header(self.yarss_config.get_config()["cookies"], torrent_url)
        id = torrent_handling.add_torrent(torrent_url, cookie_header=cookie_header)
        print "torrent added:", id
