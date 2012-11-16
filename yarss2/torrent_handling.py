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

import urllib2
from urllib2 import HTTPRedirectHandler
import os
import re
from twisted.internet import threads

from deluge.core.torrent import TorrentOptions
from deluge._libtorrent import lt
import deluge.component as component

from yarss2.yarss_email import send_email
from yarss2 import common, http
import yarss2.logger as log
from yarss2.common import GeneralSubsConf
from yarss2.lib import requests
import yarss2.torrentinfo

class TorrentDownload(object):
    def __init__(self):
        self.filedump = None
        self.error_msg = None
        self.torrent_id = None
        self.success = True
        self.torrent_url = None
        self.cookies_dict = None

    def set_error(self, error_msg):
        self.error_msg = error_msg
        self.success = False

class TorrentHandler(object):

    def __init__(self, logger):
        self.log = logger

    def listem_on_torrent_finished(self, enable=True):
        component.get("EventManager").register_event_handler("TorrentFinishedEvent", self.on_torrent_finished_event)

    def download_torrent_file(self, torrent_url, cookies_dict):
        download = TorrentDownload()
        download.torrent_url = torrent_url
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

    def add_torrent(self, torrent_url, site_cookies_dict, subscription_data=None):
        # Initialize options with default configurations
        options = TorrentOptions()

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

        if torrent_url.startswith("magnet:"):
            self.log.info("Adding magnet: '%s'" % torrent_url)
            download = TorrentDownload()
            download.torrent_id = component.get("TorrentManager").add(options=options, magnet=torrent_url)
        else:
            basename = os.path.basename(torrent_url)
            # Fix unicode URLs
            torrent_url = http.url_fix(torrent_url)
            self.log.info("Adding torrent: '%s' using cookies: %s" % (torrent_url, str(site_cookies_dict)))
            download = self.download_torrent_file(torrent_url, site_cookies_dict)
            # Error occured
            if not download.success:
                return download
            # Get the torrent data from the torrent file
            try:
                info = yarss2.torrentinfo.TorrentInfo(filedump=download.filedump)
            except Exception, e:
                self.log.debug("Unable to open torrent file: %s. Error: %s" % (torrent_url, str(e)))
                #dialogs.ErrorDialog(_("Invalid File"), e, self.dialog).run()
            download.torrent_id = component.get("TorrentManager").add(filedump=download.filedump, filename=basename, options=options)
            download.success = download.torrent_id != None
        return download

    def add_torrents(self, save_subscription_func, torrent_list, config):
        torrent_names = {}
        for torrent_match in torrent_list:
            torrent_download = self.add_torrent(torrent_match["link"],
                                                torrent_match["site_cookies_dict"],
                                                torrent_match["subscription_data"])
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
            self.send_torrent_email(config["email_configurations"],
                                    config["email_messages"][email_key],
                                    subscription_data = torrent_names[key][0],
                                    torrent_name_list = torrent_names[key][1],
                                    defered=True)

    def on_torrent_finished_event(self, torrent_id):
        print "torrent_finished_event:", torrent_id

    def send_torrent_email(self, email_configurations, email_msg, subscription_data=None,
                           torrent_name_list=None, defered=False, callback_func=None, email_data={}):
        """Send email with optional list of torrents
        Arguments:
        email_configurations - the main email configuration of YARSS2
        email_msg - a dictionary with the email data (as saved in the YARSS config)
        torrents - a tuple containing the subscription data and a list of torrent names.
        """
        self.log.info("Sending email '%s'" % email_msg["name"])
        email_data["to_address"] = email_msg["to_address"]
        email_data["subject"] = email_msg["subject"]
        email_data["message"] = email_msg["message"]

        if email_data["message"].find("$subscription_title") != -1 and subscription_data:
            email_data["message"] = email_data["message"].replace("$subscription_title", subscription_data["name"])

        if email_data["subject"].find("$subscription_title") != -1 and subscription_data:
            email_data["subject"] = email_data["subject"].replace("$subscription_title", subscription_data["name"])

        if email_data["message"].find("$torrentlist") != -1 and torrent_name_list:
            torrentlist_plain = " * %s\n" % "\n * ".join(f for f in torrent_name_list)
            msg_plain = email_data["message"].replace("$torrentlist", torrentlist_plain)
            torrentlist_html = "<ul><li>%s </li></ul>" % \
                "</li> \n <li> ".join(f for f in torrent_name_list)
            msg_html = email_data["message"]
            msg_html = email_data["message"].replace('\n', '<br/>')
            msg_html = re.sub(r'\$torrentlist(<br/>){1}?', torrentlist_html, msg_html)
            email_data["message"] = msg_plain
            email_data["message_html"] = msg_html

        # Send email with twisted to avoid waiting
        if defered:
            d = threads.deferToThread(send_email, email_data, email_configurations)
            if callback_func is not None:
                d.addCallback(callback_func)
            return d
        else:
            return send_email(email_data, email_configurations)
