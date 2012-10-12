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
import os
from twisted.internet import threads

import deluge.component as component
from deluge.core.torrent import TorrentOptions
from deluge._libtorrent import lt

from yarss2.yarss_email import send_email
from yarss2 import common, http
import yarss2.logger as log

class TorrentHandler(object):

    def __init__(self, logger):
        self.log = logger

    def download_torrent_file(self, torrent_url, cookie_header):
        filedump = None
        opener = urllib2.build_opener()

        if cookie_header.has_key("Cookie"):
            opener.addheaders.append(("Cookie", cookie_header["Cookie"]))
        try:
            webFile = opener.open(torrent_url)
            filedump = webFile.read()
        except Exception, e:
            self.log.error("Failed to download torrent url: '%s'. Exception: %s" % (torrent_url, str(e)))
            return None
        # Get the info to see if any exceptions are raised
        try:
            torrent_info = lt.torrent_info(lt.bdecode(filedump))
        except Exception, e:
            self.log.error("Unable to decode torrent file! (%s) URL: '%s'" % (str(e), torrent_url))
            return None
        return filedump

    def add_torrent(self, torrent_url, cookie_header, subscription_data=None):
        # Initialize options with default configurations
        options = TorrentOptions()

        if subscription_data is not None:
            if len(subscription_data["move_completed"]) > 0:
                options["move_completed"] = True
                options["move_completed_path"] = subscription_data["move_completed"]
            if len(subscription_data["download_location"]) > 0:
                options["download_location"] = subscription_data["download_location"]
            options["add_paused"] = subscription_data["add_torrents_in_paused_state"]

        if torrent_url.startswith("magnet:"):
            self.log.info("Adding magnet: '%s'" % torrent_url)
            torrent_id = component.get("TorrentManager").add(options=options, magnet=torrent_url)
        else:
            basename = os.path.basename(torrent_url)
            # Fix unicode URLs
            torrent_url = http.url_fix(torrent_url)
            self.log.info("Adding torrent: '%s'" % torrent_url)
            filedump = self.download_torrent_file(torrent_url, cookie_header)
            torrent_id = component.get("TorrentManager").add(filedump=filedump, filename=basename, options=options)
        return torrent_id

    def add_torrents(self, save_subscription_func, torrent_list, config):

        # Keys are the keys of the email_messages dictionary in the main config
        torrent_names = {}
        for torrent_match in torrent_list:
            if not self.add_torrent(torrent_match["link"],
                                    torrent_match["cookie_header"],
                                    torrent_match["subscription_data"]):
                self.log.warn("Failed to add torrent '%s' from url '%s'" % (torrent_match["title"], torrent_match["link"]))
            else:
                self.log.info("Succesfully added torrent '%s'." % torrent_match["title"])
                # Update subscription with date
                torrent_time = torrent_match["updated_datetime"]
                last_subscription_update = common.isodate_to_datetime(torrent_match["subscription_data"]["last_match"])
                # Update subscription time if this is newer
                # The order of the torrents is unknown, so the latest doesn't necessarily come last
                if torrent_time and last_subscription_update < torrent_time:
                    torrent_match["subscription_data"]["last_match"] = torrent_time.isoformat()
                    # Save subsription with updated timestamp
                    save_subscription_func(subscription_data=torrent_match["subscription_data"])

                # Handle email notification
                # key is the dictionary key used in the email_messages config.
                for key in torrent_match["subscription_data"]["email_notifications"].keys():
                    if not torrent_names.has_key(key):
                        torrent_names[key] = []
                    # Add the torrent file to the list of files for this notification.
                    torrent_names[key].append(torrent_match["title"])
        if config["email_configurations"]["send_email_on_torrent_events"] is False:
            return

        for email_key in torrent_names.keys():
            if not config["email_messages"][email_key]["active"]:
                continue
            # Send email in
            send_torrent_email(config["email_configurations"],
                               config["email_messages"][email_key],
                               torrent_name_list=torrent_names[key],
                               defered=True)

    def send_torrent_email(self, email_configurations, email_msg, torrent_name_list=[],
                           defered=False, callback_func=None):
        """Send email with optional list of torrents

        Arguments:
        email_configurations - the main email configuration of YARSS
        email_msg - a dictionary with the email data (as saved in the YARSS config)
        torrent_name_list - a list of strings containg the name of torrents
        """
        self.log.info("Sending email '%s'" % email_msg["name"])

        email_conf = {}
        email_conf["to_address"] = email_msg["to_address"]
        email_conf["subject"] = email_msg["subject"]
        email_conf["message"] = email_msg["message"]

        if email_conf["message"].find("$torrentlist") != -1 and torrent_name_list:
            torrentlist_plain = " * %s\n" % "\n * ".join(f for f in torrent_name_list)
            msg_plain = email_conf["message"].replace("$torrentlist", torrentlist_plain)
            torrentlist_html = "<ul><li>%s </li></ul>" % \
                "</li> \n <li> ".join(f for f in torrent_name_list)
            msg_html  = email_conf["message"].replace("$torrentlist", torrentlist_html)
            email_conf["message"] = msg_plain
            email_conf["message_html"] = msg_html

        # Send email with twisted to avoid waiting
        if defered:
            d = threads.deferToThread(send_email, email_conf, email_configurations)
            if callback_func is not None:
                d.addCallback(callback_func)
        else:
            return send_email(email_conf, email_configurations)
