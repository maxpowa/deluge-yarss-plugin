# -*- coding: utf-8 -*-
#
# test_torrent_handling.py
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
import os.path

from twisted.trial import unittest

from deluge.log import LOG as log

import yarss2.torrent_handling
from yarss2.torrent_handling import TorrentHandler, TorrentDownload
from yarss2.util.common import GeneralSubsConf, read_file
import yarss2.util.common
import common

test_component = None

class TestComponent(object):
    def __init__(self, add_retval=True):
        global test_component
        test_component = self
        self.add_success = add_retval
        self.download_success = True
        self.downloads = []
        self.added = []
        self.use_filedump = None

    def add(self, filedump=None, filename=None, options=None, magnet=None):
        download = TorrentDownload()
        download.torrent_id = ""
        download.filedump = filedump
        download.filename = filename
        download.options = options
        download.magnet = magnet
        download.add_success = self.add_success
        self.added.append(download)
        return download

    def download_torrent_file(self, torrent_url, cookies_dict):
        download = TorrentDownload()
        download.torrent_url = torrent_url
        download.cookies_dict = cookies_dict
        download.torrent_url = torrent_url
        download.success = self.download_success
        if self.use_filedump:
            download.filedump = self.use_filedump
        elif os.path.isfile(torrent_url):
            download.filedump = read_file(torrent_url)
        self.downloads.append(download)
        return download

# When replacing component with test_component in modules,
# This is called e.g. when this is executed: component.get("TorrentManager")
# we ignore the key, and return the test component
def get(key):
    return test_component

import test_torrent_handling
# This makes sure that component.get("TorrentManager") returns
# the TestComponent, and not the deluge TorrentManager.
yarss2.torrent_handling.component = test_torrent_handling

def get_file(url, cookies={}, verify=True):
    class Request(object):
        pass
    r = Request
    try:
        r.content = read_file(url)
    except Exception, e:
        pass
    return r

from yarss2.lib import requests
requests.get = get_file

class TorrentHandlingTestCase(unittest.TestCase):

    def setUp(self):
        self.log = log
        self.config = common.get_test_config()
        # get_test_config will load a new core.conf with the default values.
        # Must save to save to file so that torrent.py.TorrentOptions loads the default values
        self.config.core_config.save()
        global test_component
        test_component = TestComponent(True)

    def test_add_torrent(self):
        handler = TorrentHandler(self.log)
        filename = yarss2.util.common.get_resource("FreeBSD-9.0-RELEASE-amd64-dvd1.torrent", path="tests/data/")
        torrent_info = {"link": filename, "site_cookies_dict": {}}
        torrent_download = handler.add_torrent(torrent_info)

        torrent_added = test_component.added.pop()
        self.assertTrue(torrent_added.success)
        self.assertFalse(torrent_added.filedump is None, "Filedump is not None")
        self.assertEquals(torrent_added.filename, os.path.split(filename)[1])
        self.assertFalse(torrent_added.filedump is None)
        self.assertEquals(torrent_download.url, filename)

    def test_add_torrent_magnet_link(self):
        handler = TorrentHandler(self.log)
        torrent_url = "magnet:blbalba/url.magnet.link"
        torrent_info = {"link": torrent_url, "site_cookies_dict": {}}
        download = handler.add_torrent(torrent_info)
        self.assertTrue(download.success)
        self.assertTrue(download.is_magnet)
        self.assertEquals(test_component.added.pop().magnet, torrent_url)

    def test_add_torrent_ret_false(self):
        handler = TorrentHandler(self.log)
        torrent_url = "http://url.com/file.torrent"
        cookies_dict = {}
        global test_component
        test_component.download_success = False
        handler.download_torrent_file = test_component.download_torrent_file
        torrent_info = {"link": torrent_url, "site_cookies_dict": cookies_dict}
        torrent_download = handler.add_torrent(torrent_info)
        self.assertFalse(torrent_download.success)
        # Set by download_torrent_file
        self.assertEquals(torrent_download.torrent_url, torrent_url)
        self.assertEquals(torrent_download.cookies_dict, cookies_dict)
        test_component.download_success = True

    def test_add_torrent_with_subscription_data(self):
        handler = TorrentHandler(self.log)
        subscription_data = yarss2.yarss_config.get_fresh_subscription_config()
        subscription_data["move_completed"] = "move/path"
        subscription_data["download_location"] = "download/path"
        subscription_data["add_torrents_in_paused_state"] = GeneralSubsConf.DEFAULT

        download = TorrentDownload()
        torrent_info = {"link": "http://url.com/file.torrent",
                        "site_cookies_dict": {},
                        "subscription_data": subscription_data,
                        "torrent_download": download}

        d = handler.add_torrent(torrent_info)
        self.assertTrue(d.success)
        added = test_component.added.pop()
        self.assertTrue(added.options["move_completed"])
        self.assertEquals(added.options["move_completed_path"], subscription_data["move_completed"])
        self.assertEquals(added.options["download_location"], subscription_data["download_location"])
        # When using DEFAULT, the default value for add_paused on TorrentSettings is False
        self.assertEquals(added.options["add_paused"], False)

    def get_test_rssfeeds_match_dict(self):
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

    def test_add_torrents(self):
        handler = TorrentHandler(self.log)
        from yarss2.rssfeed_handling import RSSFeedHandler
        self.rssfeedhandler = RSSFeedHandler(self.log)

        # Override method download_torrent_file
        handler.download_torrent_file = test_component.download_torrent_file
        filename = yarss2.util.common.get_resource("FreeBSD-9.0-RELEASE-amd64-dvd1.torrent", path="tests/data/")
        test_component.use_filedump = read_file(filename)

        config = get_test_config_dict()                                # 0 is the rssfeed key
        match_result = self.rssfeedhandler.fetch_feed_torrents(config, "0")
        matching_torrents = match_result["matching_torrents"]

        saved_subscriptions = []
        def save_subscription_func(subscription_data):
            saved_subscriptions.append(subscription_data)

        handler.add_torrents(save_subscription_func, matching_torrents, self.config.get_config())
        self.assertEquals(len(saved_subscriptions), 1)
        handler.use_filedump = None

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

#import test_yarss_email
#import smtplib
#import base64
#
#class TorrentHandlingEmailTestCase(unittest.TestCase):
#
#    def setUp(self):
#        self.log = log
#        self.handler = TorrentHandler(self.log)
#        smtplib.SMTP = test_yarss_email.DummySMTP
#        self.email_config = yarss2.yarss_config.get_fresh_email_config()
#        self.email_config["from_address"] = "from@test.com"
#        self.email = {}
#        self.email["to_address"] = "test@address.com"
#        self.email["subject"] = "Test Subject"
#        self.email["message"] = "Hi\n\nThis is a test message.\n\n\nRegards"
#        self.email["name"] = "Test Message Name"
#
#        self.expected_messsage = []
#        self.expected_messsage.append('Content-Type: text/plain; charset="utf-8"')
#        self.expected_messsage.append('MIME-Version: 1.0')
#        self.expected_messsage.append('Content-Transfer-Encoding: base64')
#        self.expected_messsage.append("Subject: %s")
#        self.expected_messsage.append("From: %s")
#        self.expected_messsage.append("To: %s")
#
#        self.expected_messsage_multipart = []
#        self.expected_messsage_multipart.append('Content-Type: multipart/alternative;')
#        self.expected_messsage_multipart.append('MIME-Version: 1.0')
#        self.expected_messsage_multipart.append("Subject: %s")
#        self.expected_messsage_multipart.append("From: %s")
#        self.expected_messsage_multipart.append("To: %s")
#        self.expected_messsage_multipart.append('Content-Type: text/plain; charset="utf-8"')
#        self.expected_messsage_multipart.append('MIME-Version: 1.0')
#        self.expected_messsage_multipart.append('Content-Transfer-Encoding: base64')
#        self.expected_messsage_multipart.append('Content-Type: text/html; charset="utf-8"')
#        self.expected_messsage_multipart.append('MIME-Version: 1.0')
#        self.expected_messsage_multipart.append('Content-Transfer-Encoding: base64')
#
#    def verify_email_multipart(self, email_message, email, email_config, email_data):
#        """
#        email_message - a test_yarss_email.Message
#        email - a dictionary with the email info
#        email_config - a dictionary with the email configuration options
#        """
#        self.assertEquals(email_message.to_address, email["to_address"])
#        lines = email_message.message.splitlines()
#
#        # Content type - multipart
#        self.assertEquals(lines[0], self.expected_messsage_multipart[0])
#        # MIME version
#        self.assertEquals(lines[2], self.expected_messsage_multipart[1])
#        # Subject
#        self.assertEquals(lines[3], self.expected_messsage_multipart[2] % email["subject"])
#        # From address
#        self.assertEquals(lines[4], self.expected_messsage_multipart[3] % email_config["from_address"])
#        # To address
#        self.assertEquals(lines[5], self.expected_messsage_multipart[4] % email["to_address"])
#        # Content type text/plain
#        self.assertEquals(lines[8], self.expected_messsage_multipart[5])
#        # MIME version
#        self.assertEquals(lines[9], self.expected_messsage_multipart[6])
#        # Content transfer encoding
#        self.assertEquals(lines[10], self.expected_messsage_multipart[7])
#
#        # Message content
#        index = 12
#        message_base64 = ""
#        # Get the whole message
#        while lines[index].strip() != "":
#            message_base64 += lines[index]
#            index += 1
#
#        msg_plain_base64 = base64.b64encode(email_data["message"])
#        self.assertEquals(message_base64, msg_plain_base64)
#
#        # Content type text/html
#        self.assertEquals(lines[index + 2], self.expected_messsage_multipart[8])
#        # MIME version
#        self.assertEquals(lines[index + 3], self.expected_messsage_multipart[9])
#        # Content transfer encoding
#        self.assertEquals(lines[index + 4], self.expected_messsage_multipart[10])
#
#        message_base64 = ""
#        index  += 6
#        # Get the whole message
#        while lines[index].strip() != "":
#            message_base64 += lines[index]
#            index += 1
#
#        msg_plain_base64 = base64.b64encode(email_data["message_html"])
#        self.assertEquals(message_base64, msg_plain_base64)
#
#    def verify_email(self, email_message, email, email_config):
#        """
#        email_message - a test_yarss_email.Message
#        email - a dictionary with the email info
#        email_config - a dictionary with the email configuration options
#        """
#        self.assertEquals(email_message.to_address, email["to_address"])
#        lines = email_message.message.splitlines()
#        # Content type
#        self.assertEquals(lines[0], self.expected_messsage[0])
#        # MIME version
#        self.assertEquals(lines[1], self.expected_messsage[1])
#        # Content transfer encoding
#        self.assertEquals(lines[2], self.expected_messsage[2])
#        # Subject
#        self.assertEquals(lines[3], self.expected_messsage[3] % email["subject"])
#        # From address
#        self.assertEquals(lines[4], self.expected_messsage[4] % email_config["from_address"])
#        # To address
#        self.assertEquals(lines[5], self.expected_messsage[5] % email["to_address"])
#        # Line 7 is the entire message content encoded in base64.
#        self.assertEquals(lines[7], base64.b64encode(email["message"]))
#
#    def test_send_torrent_email_with_deferred(self):
#        def callback(args):
#            self.verify_email(test_yarss_email.smtp.get_emails().pop(), self.email, self.email_config)
#        # Send email in
#        d = self.handler.send_torrent_email(self.email_config, self.email, defered=True)
#        d.addCallback(callback)
#        return d
#
#    def test_send_torrent_email_with_deferred_with_callback(self):
#        """This test uses the callback keyword argument to add the callback
#        function to the deferred"""
#        def callback(args):
#            self.verify_email(test_yarss_email.smtp.get_emails().pop(), self.email, self.email_config)
#        # Send email in
#        d = self.handler.send_torrent_email(self.email_config, self.email, defered=True,
#                                            callback_func=callback)
#        return d
#
#    def test_send_torrent_email_multipart_with_deferred(self):
#        subscription = {"name": "Subscription name"}
#        torrent_names = ["Torrent 1", "Torrent 2"]
#        self.email["message"] = "Hi\n\nThis is a test message. \n\n$torrentlist\n\nRegards"
#        email_data = {}
#
#        def callback(args):
#            message = test_yarss_email.smtp.get_emails().pop()
#            self.verify_email_multipart(message, self.email, self.email_config, email_data)
#            # Verify that the torrent names have been inserted into the message
#            self.assertTrue(email_data["message"].find(torrent_names[0]) != -1)
#            self.assertTrue(email_data["message"].find(torrent_names[1]) != -1)
#            self.assertTrue(email_data["message_html"].find(torrent_names[0]) != -1)
#            self.assertTrue(email_data["message_html"].find(torrent_names[1]) != -1)
#
#        # Send email without deferred
#        has_sent = self.handler.send_torrent_email(self.email_config, self.email,
#                                                   torrent_name_list=torrent_names,
#                                                   subscription_data=subscription,
#                                                   defered=False, callback_func=callback,
#                                                   email_data=email_data)
#        self.assertTrue(has_sent)
#        # Send email in
#        d = self.handler.send_torrent_email(self.email_config, self.email, torrent_name_list=torrent_names,
#                                            defered=True, callback_func=callback, email_data=email_data)
#        return d
#
#
