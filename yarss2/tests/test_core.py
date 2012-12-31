# -*- coding: utf-8 -*-
#
# test_core.py
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

from twisted.trial import unittest
from twisted.python import log

from deluge.log import LOG

import yarss2.yarss_config
import yarss2.util.common
from yarss2.core import Core
from yarss2.torrent_handling import TorrentHandler, TorrentDownload

from test_torrent_handling import TestComponent
import test_torrent_handling
import common

import twisted.internet.defer as defer

class CoreTestCase(unittest.TestCase):

    def setUp(self):
        defer.setDebugging(True)
        self.config = common.get_test_config()
        # get_test_config will load a new core.conf with the default values.
        # Must save to save to file so that torrent.py.TorrentOptions loads the default values
        self.config.core_config.save()
        test_component = TestComponent()
        self.torrent_handler = TorrentHandler(LOG)
        self.torrent_handler.download_torrent_file = test_component.download_torrent_file

        # Might be necessary for changes in master branch
        #yarss2.core.component = test_component

        self.core = Core("test")
        self.core.enable(config=self.config)
        self.core.torrent_handler = self.torrent_handler

    def tearDown(self):
        # Must stop loopingcalls or test fails
        self.core.disable()

#    def test_save_rssfeed(self):
#        config = common.get_test_config()
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

    def test_initiate_rssfeed_update(self):
        config = common.get_test_config_dict()
        config["rssfeeds"]["0"]["update_interval"] = 30
        config["rssfeeds"]["0"]["obey_ttl"] = True
        config["rssfeeds"]["0"]["url"] = yarss2.util.common.get_resource(common.testdata_rssfeed_filename, path="tests")

        self.config.set_config(config)
        self.core.yarss_config = self.config

        self.add_torrents_called = False
        def add_torrents_pass(*arg):
            self.add_torrents_called = True

        self.core.rssfeed_scheduler.add_torrent_func = add_torrents_pass
        d = self.core.initiate_rssfeed_update(None, subscription_key="0")

        def callback_check(args):
            # Verify that add_torrents_pass was called
            self.assertTrue(self.add_torrents_called, "add_torrents has not been called")
        d.addCallback(callback_check)
        return d
