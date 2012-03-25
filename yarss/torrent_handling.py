#
# torrent_handling.py
#
# Copyright (C) 2012 Bro
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

import urllib2
import os

import deluge.component as component
from deluge.log import LOG as log
from deluge.core.torrent import TorrentOptions
from deluge._libtorrent import lt

from yarss.http import get_cookie_header, url_fix
from email import send_email


def download_torrent_file(torrent_url, cookie_header):
    # Fix unicode URLs
    torrent_url = url_fix(torrent_url)

    opener = urllib2.build_opener()
    
    if cookie_header.has_key("Cookie"):
        opener.addheaders.append(("Cookie", cookie_header["Cookie"]))

    webFile = opener.open(torrent_url)
    filedump = webFile.read()

    # Get the info to see if any exceptions are raised
    try:
        torrent_info = lt.torrent_info(lt.bdecode(filedump))
    except Exception, e:
        log.error("Unable to decode torrent file!: %s", e)
        name = "failed_torrent_%d.torrent"
        common.write_to_file("/home/bro/Downloads/test/torrents/" + name, filedump)
        # XXX: Probably should raise an exception here..
        return None
    return filedump

def add_torrent(torrent_url, cookie_header, subscription_data):
    basename = os.path.basename(torrent_url)
    filedump = download_torrent_file(torrent_url, cookie_header)
    
    # Initialize options with default configurations
    options = TorrentOptions()
    
    if len(subscription_data["move_completed"].strip()) > 0:
        options["move_completed"] = True
        options["move_completed_path"] = subscription_data["move_completed"].strip()

    options["add_paused"] = subscription_data["add_torrents_in_paused_state"]
    torrent_id = component.get("TorrentManager").add(filedump=filedump, filename=basename, options=options)
    return torrent_id

def add_torrents(torrent_list, config):

    for title, torrent_url, cookie_header, subscription_data in torrent_list:
        if not add_torrent(torrent_url, cookie_header, subscription_data):
            log.info("Failed to add torrent %s." % title)
        else:
            log.info("Succesfully added torrent %s." % title)
            # Send email
            
            for k in subscription_data["email_notifications"].keys():
                if subscription_data["email_notifications"][k]["on_torrent_added"]:
                    message = config["email_messages"][k]
                    if message["active"]:
                        send_email(message, config["email_configurations"])

