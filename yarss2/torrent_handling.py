#
# torrent_handling.py
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

import os

from deluge.core.torrent import TorrentOptions
from deluge._libtorrent import lt
import deluge.component as component

from yarss2.util import common, http
from yarss2.lib import requests
from yarss2.util.common import GeneralSubsConf, TorrentDownload
from yarss2.util.yarss_email import send_torrent_email
from yarss2.util import torrentinfo
import yarss2.util.logger as log

class TorrentHandler(object):

    def __init__(self, logger):
        self.log = logger

    def listem_on_torrent_finished(self, enable=True):
        component.get("EventManager").register_event_handler("TorrentFinishedEvent", self.on_torrent_finished_event)

    def download_torrent_file(self, torrent_url, cookies_dict):
        download = TorrentDownload()
        download.url = torrent_url
        download.cookies_dict = cookies_dict
        try:
            r = requests.get(torrent_url, cookies=cookies_dict, verify=False)
            download.filedump = r.content
        except Exception, e:
            error_msg = "Failed to download torrent url: '%s'. Exception: %s" % (torrent_url, str(e))
            self.log.error(error_msg)
            download.set_error(error_msg)
            return download
        # Get the info to see if any exceptions are raised
        try:
            torrent_info = lt.torrent_info(lt.bdecode(download.filedump))
        except Exception, e:
            error_msg = "Unable to decode torrent file! (%s) URL: '%s'" % (str(e), torrent_url)
            download.set_error(error_msg)
            self.log.error(error_msg)
        return download

    def get_torrent(self, torrent_info):
        url = torrent_info["link"]
        site_cookies_dict = torrent_info["site_cookies_dict"]
        download = None

        if url.startswith("magnet:"):
            self.log.info("Fetching magnet: '%s'" % url, gtkui=False)
            download = TorrentDownload({"is_magnet": True, "url": url})
        else:
            # Fix unicode URLs
            url = http.url_fix(url)
            self.log.info("Downloading torrent: '%s' using cookies: %s" % (url, str(site_cookies_dict)), gtkui=False)
            download = self.download_torrent_file(url, site_cookies_dict)
            # Error occured
            if not download.success:
                return download
            # Get the torrent data from the torrent file
            try:
                info = torrentinfo.TorrentInfo(filedump=download.filedump)
            except Exception, e:
                download.set_error("Unable to open torrent file: %s. Error: %s" % (url, str(e)))
                self.log.warn(download.error_msg)
        return download

    def add_torrent(self, torrent_info=None):
        # Initialize options with default configurations
        options = TorrentOptions()

        torrent_url = torrent_info["link"]
        site_cookies_dict = torrent_info["site_cookies_dict"],
        subscription_data = None
        if "subscription_data" in torrent_info:
            subscription_data = torrent_info["subscription_data"]

        if "torrent_download" in torrent_info:
            download = torrent_info["torrent_download"]
        else:
            download = self.get_torrent(torrent_info)

        if subscription_data is not None:
            if len(subscription_data["move_completed"]) > 0:
                options["move_completed"] = True
                options["move_completed_path"] = subscription_data["move_completed"]
            if len(subscription_data["download_location"]) > 0:
                options["download_location"] = subscription_data["download_location"]
            if subscription_data["add_torrents_in_paused_state"] != GeneralSubsConf.DEFAULT:
                options["add_paused"] = GeneralSubsConf().get_boolean(subscription_data["add_torrents_in_paused_state"])
            if subscription_data["auto_managed"] != GeneralSubsConf.DEFAULT:
                options["auto_managed"] = GeneralSubsConf().get_boolean(subscription_data["auto_managed"])
            if subscription_data.has_key("sequential_download") and subscription_data["auto_managed"] != GeneralSubsConf.DEFAULT:
                options["sequential_download"] = GeneralSubsConf().get_boolean(subscription_data["sequential_download"])
            if subscription_data["prioritize_first_last_pieces"] != GeneralSubsConf.DEFAULT:
                options["prioritize_first_last_pieces"] = GeneralSubsConf().get_boolean(subscription_data["prioritize_first_last_pieces"])

            # -2 means to use the deluge default config value, so in that case just skip
            if subscription_data["max_download_speed"] != -2:
                options["max_download_speed"] = subscription_data["max_download_speed"]
            if subscription_data["max_upload_speed"] != -2:
                options["max_upload_speed"] = subscription_data["max_upload_speed"]
            if subscription_data["max_connections"] != -2:
                options["max_connections"] = subscription_data["max_connections"]
            if subscription_data["max_upload_slots"] != -2:
                options["max_upload_slots"] = subscription_data["max_upload_slots"]

        if download.is_magnet:
            self.log.info("Adding magnet: '%s'" % torrent_url)
            download.torrent_id = component.get("TorrentManager").add(options=options, magnet=download.url)
        else:
            self.log.info("Adding torrent: '%s' using cookies: %s" % (torrent_url, str(site_cookies_dict)))
            # Error occured
            if not download.success:
                return download
            # Get the torrent data from the torrent file
            try:
                info = torrentinfo.TorrentInfo(filedump=download.filedump)
            except Exception, e:
                download.set_error("Unable to open torrent file: %s. Error: %s" % (torrent_url, str(e)))
                self.log.warn(download.error_msg)
            basename = os.path.basename(torrent_url)
            download.torrent_id = component.get("TorrentManager").add(filedump=download.filedump,
                                                                      filename=os.path.basename(torrent_url),
                                                                      options=options)
            download.success = download.torrent_id != None
            if download.success is False and download.error_msg is None:
                download.set_error("Failed to add torrent to Deluge. Is torrent already added?")
                self.log.warn(download.error_msg)
        return download

    def add_torrents(self, save_subscription_func, torrent_list, config):
        torrent_names = {}
        for torrent_match in torrent_list:
            torrent_download = self.add_torrent(torrent_match)
            if not torrent_download.success:
                self.log.warn("Failed to add torrent '%s' from url '%s'" % (torrent_match["title"], torrent_match["link"]))
            else:
                self.log.info("Succesfully added torrent '%s'." % torrent_match["title"])
                # Update subscription with date
                torrent_time = torrent_match["updated_datetime"]
                last_subscription_update = common.isodate_to_datetime(torrent_match["subscription_data"]["last_match"])
                # Update subscription time if this is newer
                # The order of the torrents are in ordered from newest to oldest
                if torrent_time and last_subscription_update < torrent_time:
                    torrent_match["subscription_data"]["last_match"] = torrent_time.isoformat()
                    # Save subsription with updated timestamp
                    save_subscription_func(subscription_data=torrent_match["subscription_data"])

                # Handle email notification
                # key is the dictionary key used in the email_messages config.
                for key in torrent_match["subscription_data"]["email_notifications"].keys():
                    # Must be enabled in the subscription
                    if not torrent_match["subscription_data"]["email_notifications"][key]["on_torrent_added"]:
                        continue
                    if not torrent_names.has_key(key):
                        torrent_names[key] = (torrent_match["subscription_data"], [])
                    # Add the torrent file to the list of files for this notification.
                    torrent_names[key][1].append(torrent_match["title"])
        if config["email_configurations"]["send_email_on_torrent_events"] is False:
            return

        for email_key in torrent_names.keys():
            # Check that the message is active
            if not config["email_messages"][email_key]["active"]:
                continue
            # Send email in
            send_torrent_email(config["email_configurations"],
                                    config["email_messages"][email_key],
                                    subscription_data = torrent_names[key][0],
                                    torrent_name_list = torrent_names[key][1],
                                    defered=True)

    def on_torrent_finished_event(self, torrent_id):
        print "torrent_finished_event:", torrent_id

