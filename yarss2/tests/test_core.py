# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2019 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.trial import unittest

import logging
LOG = logging.getLogger(__name__)

import yarss2.yarss_config
import yarss2.util.common
from yarss2.core import Core
from yarss2.torrent_handling import TorrentHandler, TorrentDownload
from yarss2.yarss_config import get_user_agent

from .test_torrent_handling import TestComponent
from . import test_torrent_handling
from . import common as test_common


import twisted.internet.defer as defer

test_common.disable_new_release_check()


class CoreTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        defer.setDebugging(True)
        self.config = test_common.get_test_config()
        # get_test_config will load a new core.conf with the default values.
        # Must save to save to file so that torrent.py.TorrentOptions loads the default values
        self.config.core_config.save()
        test_component = TestComponent()
        self.torrent_handler = TorrentHandler(LOG)
        self.torrent_handler.download_torrent_file = test_component.download_torrent_file

        # Might be necessary for changes in master branch
        # yarss2.core.component = test_component

        self.core = Core("test")
        self.core.enable(config=self.config)
        self.core.torrent_handler = self.torrent_handler

    def tearDown(self):  # NOQA
        # Must stop loopingcalls or test fails
        self.core.disable()

#    def test_save_rssfeed(self):
#        config = test_common.get_test_config()
#        rssfeed = yarss2.yarss_config.get_fresh_rssfeed_config()
#
#        core = Core("YaRSS2")
#        core.enable(config=config)
#
#        core.save_rssfeed(self, dict_key=None, rssfeed_data=rssfeed, delete=False)
#
#        #default_subscription = yarss2.yarss_config.get_fresh_subscription_config()

    def test_add_torrent(self):
        torrent_name = "FreeBSD-9.0-RELEASE-amd64-dvd1.torrent"
        torrent_url = yarss2.util.common.get_resource(torrent_name, path="tests/data/")
        torrent_info = {"link": torrent_url}
        download_dict = self.core.add_torrent(torrent_info)
        download = TorrentDownload(download_dict)

        self.assertTrue(download.success, "Download failed, but should be True")
        self.assertEquals(torrent_url, test_torrent_handling.test_component.downloads.pop().torrent_url)
        self.assertEquals(test_torrent_handling.test_component.added.pop().filename, torrent_name)

    def test_add_torrent_default_user_agent(self):
        torrent_name = "FreeBSD-9.0-RELEASE-amd64-dvd1.torrent"
        torrent_url = yarss2.util.common.get_resource(torrent_name, path="tests/data/")
        torrent_info = {"link": torrent_url, "rssfeed_key": "0"}
        config = test_common.get_test_config_dict()
        default_user_agent = get_user_agent()
        self.config.set_config(config)
        self.core.yarss_config = self.config

        download_dict = self.core.add_torrent(torrent_info)
        self.assertEquals(download_dict["headers"]["User-Agent"], default_user_agent)

    def test_add_torrent_custom_user_agent(self):
        torrent_name = "FreeBSD-9.0-RELEASE-amd64-dvd1.torrent"
        torrent_url = yarss2.util.common.get_resource(torrent_name, path="tests/data/")
        torrent_info = {"link": torrent_url, "rssfeed_key": "0"}
        config = test_common.get_test_config_dict()
        custom_user_agent = "Custom user agent test"
        config["rssfeeds"]["0"]["user_agent"] = custom_user_agent
        self.config.set_config(config)
        self.core.yarss_config = self.config

        download_dict = self.core.add_torrent(torrent_info)
        self.assertEquals(download_dict["headers"]["User-Agent"], custom_user_agent)

    def test_initiate_rssfeed_update(self):
        config = test_common.get_test_config_dict()
        config["rssfeeds"]["0"]["update_interval"] = 30
        config["rssfeeds"]["0"]["obey_ttl"] = True
        config["rssfeeds"]["0"]["url"] = yarss2.util.common.get_resource(test_common.testdata_rssfeed_filename, path="tests")

        self.config.set_config(config)
        self.core.yarss_config = self.config

        self.add_torrents_called = False

        def add_torrents_pass(*arg):
            self.add_torrents_called = True

        self.core.rssfeed_scheduler.add_torrents_func = add_torrents_pass
        d = self.core.initiate_rssfeed_update(None, subscription_key="0")

        def callback_check(args):
            # Verify that add_torrents_pass was called
            self.assertTrue(self.add_torrents_called, "add_torrents has not been called")

        d.addCallback(callback_check)
        return d
