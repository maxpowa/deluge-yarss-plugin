#
# logger.py
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

import deluge.component as component
from deluge.event import DelugeEvent
from deluge.log import LOG as log

from yarss2.util import common
from yarss2.util.gtkui_log import GtkUILogMessageEvent

class Logger(object):

    def __init__(self, gtkui_logger=None):
        self.gtkui_logger = gtkui_logger

    def handle_gtkui_log(self, message, gtkui):
        if not gtkui:
            return
        # On gtkui client
        if self.gtkui_logger:
            self.gtkui_logger.gtkui_log_message(message)
        else: # On deluge daemon
            self.gtkui_log_message_event(message)

    def debug(self, message, gtkui=True):
        log.debug(self._msg(message))
        self.handle_gtkui_log(message, gtkui)

    def info(self, message, gtkui=True):
        log.info(self._msg(message))
        self.handle_gtkui_log(message, gtkui)

    def warn(self, message, gtkui=True):
        log.warn(self._msg(message))
        self.handle_gtkui_log(message, gtkui)

    def error(self, message, gtkui=True):
        log.error(self._msg(message))
        self.handle_gtkui_log(message, gtkui)

    def _msg(self, msg):
        return "%s.%s:%s: %s" % ("YaRSS2", common.filename(), common.linenumber(), msg)

    def gtkui_log_message_event(self, message):
        try:
            # Tests throws KeyError for EventManager when running this method, so wrap this in try/except
            component.get("EventManager").emit(GtkUILogMessageEvent(message))
        except KeyError:
            pass
