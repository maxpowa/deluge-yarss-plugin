#
# gtkui_log.py
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

from deluge.event import DelugeEvent

from yarss2.util.common import get_current_date_in_isoformat

class GTKUI_logger(object):
    """This class handles messages going to the GTKUI log message pane"""

    def __init__(self, textview):
        self.textview = textview

    def gtkui_log_message(self, message):
        def add_msg():
            buf = self.textview.get_buffer()
            time = get_current_date_in_isoformat()
            msg_to_append = "(%s): %s" % (time, message)
            buf.insert(buf.get_end_iter(),  msg_to_append + "\n")
        import gobject # Do not import on top as only the client needs to have this package
        gobject.idle_add(add_msg)

class GtkUILogMessageEvent(DelugeEvent):
    """
    Emitted when a message has been written to the log.
    """
    def __init__(self, message):
        """
        :param message: the message to be logged
        """
        self._args = [message]
