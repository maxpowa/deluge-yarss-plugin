# -*- coding: utf-8 -*-
#
# test_yarss_config.py
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

import yarss2.yarss_config
import common

smtp = None
inbox = []

class Message(object):
    def __init__(self, from_address, to_address, message):
        self.from_address = from_address
        self.to_address = to_address
        self.message = message

class DummySMTP(object):
    def __init__(self, server_address, port):
        self.server_address = server_address
        self.port = port
        global smtp
        smtp = self
        self.ehlo_called = False
        self.starttls_called = False

    def login(self, username, password):
        self.username = username
        self.password = password

    def sendmail(self, from_address, to_address, fullmessage):
        global inbox
        inbox.append(Message(from_address,to_address,fullmessage))
        return []

    def quit(self):
        self.has_quit = True

    def ehlo(self):
        self.ehlo_called = True

    def starttls(self):
        self.starttls_called = True

    def get_emails(self):
        global inbox
        return inbox

import yarss2.yarss_config
from yarss2.yarss_email import send_email

import smtplib
smtplib.SMTP = DummySMTP

class YaRSS2EmailTestCase(unittest.TestCase):

    def setUp(self):
        self.config = common.get_test_config()

    def test_send_email(self):
        email_config = yarss2.yarss_config.get_fresh_email_config()
        email_config["from_address"] = "from@test.com"

        email = {}
        email["to_address"] = "test@address.com"
        email["subject"] = "Test Subject"
        email["message"] = "Test Message"

        global smtp
        global inbox
        self.assertTrue(send_email(email, email_config))
        self.assertEquals(inbox[0].from_address, email_config["from_address"])
        self.assertEquals(inbox[0].to_address, email["to_address"])
        self.assertEquals(smtp.server_address, email_config["smtp_server"])
        self.assertEquals(smtp.port, smtplib.SMTP_PORT)

    def test_send_email_with_auth(self):
        email_config = yarss2.yarss_config.get_fresh_email_config()
        email_config["from_address"] = "from@test.com"
        email_config["smtp_server"] = "server_address"
        email_config["smtp_port"] = "43353"
        email_config["smtp_authentication"] = True
        email_config["smtp_username"] = "testuser"
        email_config["smtp_password"] = "testpw"

        email = {}
        email["to_address"] = "test@address.com"
        email["subject"] = "Test Subject"
        email["message"] = "Test Message"

        global smtp
        global inbox
        self.assertTrue(send_email(email, email_config))
        self.assertEquals(inbox[0].from_address, email_config["from_address"])
        self.assertEquals(inbox[0].to_address, email["to_address"])
        self.assertEquals(smtp.server_address, email_config["smtp_server"])
        self.assertEquals(smtp.port, int(email_config["smtp_port"]))
        self.assertEquals(smtp.username, email_config["smtp_username"])
        self.assertEquals(smtp.password, email_config["smtp_password"])

        self.assertTrue(smtp.ehlo_called)
        self.assertTrue(smtp.starttls_called)
