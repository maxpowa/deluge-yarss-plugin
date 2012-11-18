#
# email.py
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

import re

from twisted.internet import threads

import yarss2.util.logger
import yarss2.util.common as log

# Mime (might) not be included with Deluge on Windows.
try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except ImportError, e:
    from yarss2.lib.mime.multipart import MIMEMultipart
    from yarss2.lib.mime.text import MIMEText

import smtplib

log = yarss2.util.logger.Logger()

def send_email(email_conf, server_conf):
    """sends email notification of finished torrent"""
    # Send multipart message with text and html
    if email_conf.has_key("message"):
        # Send Multipart email
        if email_conf.has_key("message_html"):
            mime_message = MIMEMultipart("alternative")
            msg_plain = MIMEText(email_conf["message"].encode('utf-8'), "plain", _charset='utf-8')
            msg_html = MIMEText(email_conf["message_html"].encode('utf-8'), "html", _charset='utf-8')
            mime_message.attach(msg_plain)
            mime_message.attach(msg_html)
        else:
            # Send plain message
            mime_message = MIMEText(email_conf["message"].encode('utf-8'), "plain", _charset='utf-8')
    elif email_conf.has_key("message_html"):
        # Send html message
        mime_message = MIMEText(email_conf["message"].encode('utf-8'), "html", _charset='utf-8')
    else:
        log.warn("Email config must contain either 'message' or 'message_html'")
        return False

    mime_message["Subject"] = email_conf["subject"]
    mime_message["From"] = server_conf["from_address"]
    mime_message["To"] = email_conf["to_address"]

    port = smtplib.SMTP_PORT
    if len(server_conf["smtp_port"].strip()) > 0:
        try:
            port = int(server_conf["smtp_port"])
        except:
            pass
    try:
        mailServer = smtplib.SMTP(server_conf["smtp_server"], port)
    except Exception, e:
        log.error("There was an error sending the notification email: %s" % str(e))
        return False

    log.info("Sending email message:\nTo: %s\nFrom: %s\nSubject: %s\n" % \
                 (mime_message["To"], mime_message["From"], mime_message["Subject"]))
    log.info("Server: %s, port: %s, authentication: %s" % (server_conf["smtp_server"],
                                                           server_conf["smtp_port"],
                                                           server_conf["smtp_authentication"]))
    if server_conf["smtp_authentication"]:
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        try:
            mailServer.login(server_conf["smtp_username"], server_conf["smtp_password"])
        except smtplib.SMTPHeloError:
            log.warn("The server didn't reply properly to the helo greeting")
        except smtplib.SMTPAuthenticationError:
            log.warn("The server didn't accept the username/password combination")
    try:
        mailServer.sendmail(server_conf["from_address"], email_conf["to_address"], mime_message.as_string())
        mailServer.quit()
    except Exception, e:
        log.error("Sending email notification failed: %s", e)
        return False
    else:
        log.info("Sending email notification of finished torrent was successful")
    return True


def send_torrent_email(email_configurations, email_msg, subscription_data=None,
                       torrent_name_list=None, defered=False, callback_func=None, email_data={}):
    """Send email with optional list of torrents
    Arguments:
    email_configurations - the main email configuration of YARSS2
    email_msg - a dictionary with the email data (as saved in the YARSS config)
    torrents - a tuple containing the subscription data and a list of torrent names.
    """
    log.info("Sending email '%s'" % email_msg["name"])
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
