#
# core.py
#
# Copyright (C) 2012 Bro
#
# Based on work by:
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

from deluge.plugins.pluginbase import CorePluginBase
from deluge.core.rpcserver import export

from yarss2.yarss_config import YARSSConfig
from yarss2.torrent_handling import TorrentHandler
from yarss2.rssfeed_scheduler import RSSFeedScheduler
import yarss2.util.logger
import yarss2.util.common
from yarss2.util.http import get_matching_cookies_dict

class Core(CorePluginBase):

    def __init__(self, name):
        """Used for tests only"""
        if name is not "test":
            super(Core, self).__init__(name)
        else:
            # To avoid warnings when running tests
            self._component_name = name

    def enable(self, config=None):
        self.log = yarss2.util.logger.Logger()
        self.torrent_handler = TorrentHandler(self.log)
        if config is None:
            self.yarss_config = YARSSConfig(self.log)
        else:
            self.yarss_config = config
        self.rssfeed_scheduler = RSSFeedScheduler(self.yarss_config, self.log)
        self.rssfeed_scheduler.enable_timers()
        self.log.info("Enabled YaRSS2 %s" % yarss2.util.common.get_version())

    def disable(self):
        self.yarss_config.save()
        self.rssfeed_scheduler.disable_timers()

    def update(self):
        pass

    @export
    def initiate_rssfeed_update(self, rssfeed_key, subscription_key=None):
        return self.rssfeed_scheduler.queue_rssfeed_update(rssfeed_key, subscription_key=subscription_key)

    @export
    def get_config(self):
        "Returns the config dictionary"
        return self.yarss_config.get_config()

    @export
    def save_email_configurations(self, email_configurations):
        conf = {"email_configurations": email_configurations}
        try:
            self.yarss_config.set_config(conf)
        except ValueError as (v):
            self.log.error("Failed to save email configurations:" + str(v))

    @export
    def save_subscription(self, dict_key=None, subscription_data=None, delete=False):
        """Saves the subscription in subscription_data.
        If subscription_data is None and delete=True, delete subscription with key==dict_key
        """
        if delete:
            if subscription_data is not None:
                self.log.warn("save_subscription called with delete=True, but rssfeed_data is not None!")
            else:
                self.log.info("Deleting Subscription '%s'" %
                         self.yarss_config.get_config()["subscriptions"][dict_key]["name"])
        try:
            return self.yarss_config.generic_save_config("subscriptions", dict_key=dict_key,
                                                         data_dict=subscription_data, delete=delete)
        except ValueError as (v):
            self.log.error("Failed to save subscription:" + str(v))
        return None

    @export
    def save_rssfeed(self, dict_key=None, rssfeed_data=None, delete=False):
        """Saves the rssfeed in rssfeed_data.
        If rssfeed_data is None and delete=True, delete rssfeed with key==dict_key
        """
        try:
            if delete:
                if rssfeed_data is not None:
                    self.log.warn("save_rssfeed called with delete=True, but rssfeed_data is not None!")
                else:
                    self.log.info("Stopping and deleting RSS Feed '%s'" %
                             self.yarss_config.get_config()["rssfeeds"][dict_key]["name"])

            config = self.yarss_config.generic_save_config("rssfeeds", dict_key=dict_key,
                                                         data_dict=rssfeed_data, delete=delete)
            if delete is True:
                self.rssfeed_scheduler.delete_timer(dict_key)
            # Successfully saved rssfeed, check if timer was changed
            elif config:
                if self.rssfeed_scheduler.set_timer(rssfeed_data["key"], rssfeed_data["update_interval"]):
                    self.log.info("Scheduled RSS Feed '%s' with interval %s" %
                             (rssfeed_data["name"], rssfeed_data["update_interval"]))
            return config
        except ValueError as (v):
            self.log.error("Failed to save rssfeed:" + str(v))

    @export
    def save_cookie(self, dict_key=None, cookie_data=None, delete=False):
        """Save cookie to config.
        If cookie_data is None and delete=True, delete cookie with key==dict_key"""
        if cookie_data:
            if type(cookie_data["value"]) is not dict:
                self.log.error("Cookie value must be a dictionary!")
                return None
        try:
            return self.yarss_config.generic_save_config("cookies", dict_key=dict_key,
                                                         data_dict=cookie_data, delete=delete)
        except ValueError as (v):
            self.log.error("Failed to save cookie:" + str(v))

    @export
    def save_email_message(self, dict_key=None, message_data=None, delete=False):
        """Save email message to config.
        If message_data is None, delete message with key==dict_key"""
        try:
            return self.yarss_config.generic_save_config("email_messages", dict_key=dict_key,
                                                         data_dict=message_data, delete=delete)
        except ValueError as (v):
            self.log.error("Failed to save email message:" + str(v))

    @export
    def add_torrent(self, torrent_info):
        site_cookies_dict = get_matching_cookies_dict(self.yarss_config.get_config()["cookies"], torrent_info["link"])
        torrent_info["site_cookies_dict"] = site_cookies_dict
        torrent_download = self.torrent_handler.add_torrent(torrent_info)
        return torrent_download.to_dict()
