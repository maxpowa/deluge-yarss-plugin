# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os

import requests

import deluge.component as component
from deluge._libtorrent import lt
from deluge.core.torrent import TorrentOptions
from deluge.error import AddTorrentError

from yarss2.util import common, http, torrentinfo
from yarss2.util.common import GeneralSubsConf, TorrentDownload
from yarss2.util.yarss_email import send_torrent_email


class TorrentHandler(object):

    def __init__(self, logger):
        self.log = logger

    def listen_on_torrent_finished(self, enable=True):
        component.get("EventManager").register_event_handler("TorrentFinishedEvent", self.on_torrent_finished_event)

    def download_torrent_file(self, torrent_url, cookies=None, headers=None):
        download = TorrentDownload()
        download.url = torrent_url
        download.cookies = cookies
        args = {"verify": False}
        if cookies is not None:
            args["cookies"] = cookies
        if headers is not None:
            args["headers"] = headers
        download.headers = headers
        try:
            r = requests.get(torrent_url, **args)
            download.filedump = r.content
        except Exception as e:
            error_msg = "Failed to download torrent url: '%s'. Exception: %s" % (torrent_url, str(e))
            self.log.error(error_msg)
            download.set_error(error_msg)
            return download

        if download.filedump is None:
            error_msg = "Filedump is None"
            download.set_error(error_msg)
            self.log.warning(error_msg)
            return download

        try:
            # Get the info to see if any exceptions are raised
            lt.torrent_info(lt.bdecode(download.filedump))
        except Exception as e:
            error_msg = "Unable to decode torrent file! (%s) URL: '%s'" % (str(e), torrent_url)
            download.set_error(error_msg)
            self.log.error(error_msg)
        return download

    def get_torrent(self, torrent_info):
        url = torrent_info["link"]
        site_cookies_dict = torrent_info.get("site_cookies_dict", None)
        download = None
        headers = {}
        user_agent = torrent_info.get("user_agent", None)

        if user_agent:
            headers["User-Agent"] = user_agent

        if url.startswith("magnet:"):
            self.log.info("Fetching magnet: '%s'" % url, gtkui=False)
            download = TorrentDownload({"is_magnet": True, "url": url})
        else:
            # Fix unicode URLs
            url = http.url_fix(url)
            self.log.info("Downloading torrent: '%s' using cookies: '%s', headers: '%s'" %
                          (url, str(site_cookies_dict), str(headers)), gtkui=True)
            download = self.download_torrent_file(url, cookies=site_cookies_dict, headers=headers)
            # Error occured
            if not download.success:
                return download
            # Get the torrent data from the torrent file
            try:
                torrentinfo.TorrentInfo(filedump=download.filedump)
            except Exception as e:
                download.set_error("Unable to open torrent file: %s. Error: %s" % (url, str(e)))
                self.log.warning(download.error_msg)
        return download

    def add_torrent(self, torrent_info):
        # Initialize options with default configurations
        options = TorrentOptions()
        torrent_url = torrent_info["link"]
        subscription_data = torrent_info.get("subscription_data", None)

        if "torrent_download" in torrent_info:
            download = torrent_info["torrent_download"]
        else:
            download = self.get_torrent(torrent_info)

        if subscription_data:
            sub_folder = None
            if torrent_info["folder"]:
                self.log.info("Torrent info specifies folder: '%s'" % torrent_info["folder"], gtkui=False)
                # Sanitize the folder to avoid directory traversal, can still traverse down
                sub_folder = torrent_info["folder"].replace("..\\","").replace("../","")
                sub_folder = sub_folder.translate(str.maketrans('','',':*?"<>|')) # Remove disallowed chars
                sub_folder = os.path.normpath(sub_folder.lstrip('\\/'))
            if len(subscription_data["move_completed"]) > 0:
                options["move_completed"] = True
                options["move_completed_path"] = subscription_data["move_completed"]
                if sub_folder:
                    options["move_completed_path"] = os.path.join(options["move_completed_path"],sub_folder)
            if len(subscription_data["download_location"]) > 0:
                options["download_location"] = subscription_data["download_location"]
                if sub_folder:
                    options["download_location"] = os.path.join(options["download_location"],sub_folder)
            if subscription_data["add_torrents_in_paused_state"] != GeneralSubsConf.DEFAULT:
                options["add_paused"] = GeneralSubsConf().get_boolean(subscription_data["add_torrents_in_paused_state"])
            if subscription_data["auto_managed"] != GeneralSubsConf.DEFAULT:
                options["auto_managed"] = GeneralSubsConf().get_boolean(subscription_data["auto_managed"])
            if "sequential_download" in subscription_data and\
               subscription_data["auto_managed"] != GeneralSubsConf.DEFAULT:
                options["sequential_download"] = GeneralSubsConf().get_boolean(subscription_data["sequential_download"])
            if subscription_data["prioritize_first_last_pieces"] != GeneralSubsConf.DEFAULT:
                options["prioritize_first_last_pieces"] = GeneralSubsConf().get_boolean(
                    subscription_data["prioritize_first_last_pieces"])

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
            download.torrent_id = component.get("TorrentManager").add(options=options,
                                                                      magnet=download.url)
        else:
            # Error occured
            if not download.success:
                self.log.warning("Failed to add '%s'." % (torrent_url))
                return download

            self.log.info("Adding torrent: '%s'." % (torrent_url))
            # Get the torrent data from the torrent file
            try:
                torrentinfo.TorrentInfo(filedump=download.filedump)
            except Exception as e:
                download.set_error("Unable to open torrent file: %s. Error: %s" % (torrent_url, str(e)))
                self.log.warning(download.error_msg)

            try:
                download.torrent_id = component.get("TorrentManager").add(filedump=download.filedump,
                                                                          filename=os.path.basename(torrent_url),
                                                                          options=options)
            except AddTorrentError as err:
                download.success = False
                download.set_error("Failed to add torrent to Deluge: %s" % (str(err)))
                self.log.warning(download.error_msg)
            else:
                if ("Label" in component.get("Core").get_enabled_plugins()
                        and subscription_data and subscription_data.get("label", "")):
                    component.get("CorePlugin.Label").set_torrent(download.torrent_id, subscription_data["label"])

        return download

    def add_torrents(self, save_subscription_func, torrent_list, config):
        torrent_names = {}
        for torrent_match in torrent_list:
            torrent_download = self.add_torrent(torrent_match)

            if not torrent_download.success:
                self.log.warning("Failed to add torrent '%s' from url '%s'" %
                                 (torrent_match["title"], torrent_match["link"]))
            else:
                self.log.info("Succesfully added torrent '%s'." % torrent_match["title"])
                # Update subscription with date
                torrent_time = torrent_match["updated_datetime"]

                last_subscription_update = common.isodate_to_datetime(
                    torrent_match["subscription_data"]["last_match"])

                last_subscription_update = common.datetime_ensure_timezone(last_subscription_update)
                # Update subscription time if this is newer
                # The order of the torrents are in ordered from newest to oldest
                if torrent_time and last_subscription_update <= torrent_time:
                    torrent_match["subscription_data"]["last_match"] = torrent_time.isoformat()
                    # Save subsription with updated timestamp
                    save_subscription_func(subscription_data=torrent_match["subscription_data"])

                # Handle email notification
                # key is the dictionary key used in the email_messages config.
                for key in torrent_match["subscription_data"]["email_notifications"].keys():
                    # Must be enabled in the subscription
                    if not torrent_match["subscription_data"]["email_notifications"][key]["on_torrent_added"]:
                        continue
                    if key not in torrent_names:
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
                               subscription_data=torrent_names[key][0],
                               torrent_name_list=torrent_names[key][1],
                               deferred=True)

    def on_torrent_finished_event(self, torrent_id):
        pass
