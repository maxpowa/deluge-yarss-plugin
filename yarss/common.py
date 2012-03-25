#
# common.py
#
# Copyright (C) 2012 Bro
#
# Based on work by:
# Copyright (C) 2009 Camillo Dell'mour <cdellmour@gmail.com>
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

import pkg_resources
import datetime
import os


def get_resource(filename):
    return pkg_resources.resource_filename("yarss", os.path.join("data", filename))

def get_default_date():
    return datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)

def get_selected_in_treeview(treeview, store):
    """Helper to get the key of the selected element in the given treeview
    return None of no item is selected.
    The key must be in the first column of the ListStore
    """
    tree, tree_id = treeview.get_selection().get_selected()
    if tree_id:
        key = str(store.get_value(tree_id, 0))
        return key
    return None

def write_to_file(filepath, content):
    count = 0
    while os.path.isfile(filepath % count):
        count += 1
    filepath = filapath % count
    local_file = open(filepath, "w")
    local_file.write(content)
    local_file.close()

