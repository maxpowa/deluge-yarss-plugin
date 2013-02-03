#
# path_chooser.py
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

from deluge.ui.client import client

import yarss2.util.logger as log
from yarss2.gtkui.path_combo_chooser import PathChooserComboBox

class PathChooser(PathChooserComboBox):

    def __init__(self, config_key):
        self.config_key = config_key
        PathChooserComboBox.__init__(self)
        self.set_auto_completer_func(self.on_completion)
        self.connect("list-value-added", self.path_added_event)

    def on_completion(self, value):
        def on_paths_cb(paths):
            self.complete(value, paths)
        d = client.yarss2.get_path_completion(value)
        d.addCallback(on_paths_cb)

    def path_added_event(self, widget, values):
        config = {self.config_key: self.get_values()}
        client.core.set_config(config)
