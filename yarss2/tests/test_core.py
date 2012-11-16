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

from deluge.log import LOG as log

import yarss2.yarss_config
from yarss2.core import Core
from yarss2.torrent_handling import TorrentHandler, TorrentDownload
from test_torrent_handling import TestComponent

import test_torrent_handling
import common

class CoreTestCase(unittest.TestCase):

    def setUp(self):
        self.config = common.get_test_config()
        # get_test_config will load a new core.conf with the default values.
        # Must save to save to file so that torrent.py.TorrentOptions loads the default values
        self.config.core_config.save()
        test_component = TestComponent()

        self.handler = TorrentHandler(log)
        self.handler.download_torrent_file = test_component.download_torrent_file

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
        core = Core("test")
        core.torrent_handler = self.handler
        torrent_url = "http://url...com"
        core.yarss_config = self.config
        success = core.add_torrent(torrent_url)
        self.assertTrue(success)
        self.assertEquals(torrent_url, test_torrent_handling.test_component.downloads.pop().torrent_url)
        self.assertEquals(test_torrent_handling.test_component.added.pop().filename, "url...com")

    def test_enable(self):
        """Verify that it runs"""
        core = Core("test")
        core.enable(config=self.config)
