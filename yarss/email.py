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

from deluge.log import LOG as log

import smtplib


def send_email(email_conf, server_conf):
    """sends email notification of finished torrent"""

    print "send_email:", email_conf
    print "serve_conf:", server_conf

    headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        server_conf["from_address"], email_conf["to_address"], email_conf["subject"])

    port = 25
    message = headers + email_conf["message"]
    if len(server_conf["smtp_port"]) > 0:
        port = int(server_conf["smtp_port"])
#    else:
#        if server_conf["ntf_security"] == 'SSL':
#            port = 465
#        elif self.config["ntf_security"] == 'TLS':
#            port = 587
#        elif self.config["ntf_security"] is None:
#            port = 25
    try:
        mailServer = smtplib.SMTP(server_conf["smtp_server"], port)
    except Exception, e:
        log.error("There was an error sending the notification email: %s", e)
        return False

    log.info("Sending email message: %s" % message)
    log.info("Server: %s, port: %s, authentication: %s" % (server_conf["smtp_server"], 
                                                           server_conf["smtp_port"], 
                                                           server_conf["smtp_authentication"]))

    if server_conf["smtp_authentication"]:
        #if self.config["ntf_security"] == 'SSL' or 'TLS':
        #if self.config["ntf_security"] == 'SSL' or 'TLS':
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        try:
            mailServer.login(server_conf["smtp_username"], server_conf["smtp_password"])
        except smtplib.SMTPHeloError:
            log.warning("The server didn't reply properly to the helo greeting")
        except smtplib.SMTPAuthenticationError:
            log.warning("The server didn't accept the username/password combination")
    try:
        mailServer.sendmail(server_conf["from_address"], email_conf["to_address"], message)
        mailServer.quit()
    except:
        log.warning("Sending email notification failed")
        return False
    else:
        log.info("sending email notification of finished torrent was successful")
    return True
