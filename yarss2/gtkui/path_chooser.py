# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
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
