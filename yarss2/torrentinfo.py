# -*- coding: utf-8 -*-
#
# torrentinfo.py
#
# Copyright (C) 2012 Bro
#
# Based on work by:
#
# Copyright (C) Damien Churchill 2008-2009 <damoxc@gmail.com>
# Copyright (C) Andrew Resch 2009 <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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
#

"""
The ui common module contains methods and classes that are deemed useful for
all the interfaces.
"""

import os

try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from deluge import bencode
from deluge.common import decode_string
from deluge.ui.common import FileTree, FileTree2
#from deluge.log import LOG as log
#import deluge.configmanager
import yarss2.logger as log

class TorrentInfo(object):
    """
    Collects information about a torrent file.

    :param filename: The path to the torrent
    :type filename: string

    """
    def __init__(self, filename=None, filedump=None, filetree=1):
        if not filename and not filedump:
            log.error("Both filename and filedump are None!")
            return
        self.filename = None
        if filename:
            self.filename = filename
            # Read the torrent from file
            try:
                log.debug("Attempting to open %s.", filename)
                self.__m_filedata = open(filename, "rb").read()
            except Exception, e:
                log.warning("Unable to open %s: %s", filename, e)
                raise e
        else:
            self.__m_filedata = filedump

    def parse(self, filetree=1):
        if not self.__m_filedata:
            log.error("No data to process!")
            return
        try:
            self.__m_metadata = bencode.bdecode(self.__m_filedata)
        except Exception, e:
            log.warning("Failed to decode torrent data %s: %s", self.filename if self.filename else "", e)
            raise e

        self.__m_info_hash = sha(bencode.bencode(self.__m_metadata["info"])).hexdigest()

        # Get encoding from torrent file if available
        self.encoding = None
        if "encoding" in self.__m_metadata:
            self.encoding = self.__m_metadata["encoding"]
        elif "codepage" in self.__m_metadata:
            self.encoding = str(self.__m_metadata["codepage"])
        if not self.encoding:
            self.encoding = "UTF-8"

        # Check if 'name.utf-8' is in the torrent and if not try to decode the string
        # using the encoding found.
        if "name.utf-8" in self.__m_metadata["info"]:
            self.__m_name = decode_string(self.__m_metadata["info"]["name.utf-8"])
        else:
            self.__m_name = decode_string(self.__m_metadata["info"]["name"], self.encoding)

        # Get list of files from torrent info
        paths = {}
        dirs = {}
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for index, f in enumerate(self.__m_metadata["info"]["files"]):
                if "path.utf-8" in f:
                    path = os.path.join(prefix, *f["path.utf-8"])
                else:
                    path = decode_string(os.path.join(prefix, decode_string(os.path.join(*f["path"]), self.encoding)), self.encoding)
                f["index"] = index
                paths[path] = f

                dirname = os.path.dirname(path)
                while dirname:
                    dirinfo = dirs.setdefault(dirname, {})
                    dirinfo["length"] = dirinfo.get("length", 0) + f["length"]
                    dirname = os.path.dirname(dirname)

            if filetree == 2:
                def walk(path, item):
                    if item["type"] == "dir":
                        item.update(dirs[path])
                    else:
                        item.update(paths[path])
                    item["download"] = True

                file_tree = FileTree2(paths.keys())
                file_tree.walk(walk)
            else:
                def walk(path, item):
                    if type(item) is dict:
                        return item
                    return [paths[path]["index"], paths[path]["length"], True]

                file_tree = FileTree(paths)
                file_tree.walk(walk)
            self.__m_files_tree = file_tree.get_tree()
        else:
            if filetree == 2:
                self.__m_files_tree = {
                    "contents": {
                        self.__m_name: {
                            "type": "file",
                            "index": 0,
                            "length": self.__m_metadata["info"]["length"],
                            "download": True
                        }
                    }
                }
            else:
                self.__m_files_tree = {
                    self.__m_name: (0, self.__m_metadata["info"]["length"], True)
                }

        self.__m_files = []
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for f in self.__m_metadata["info"]["files"]:
                if "path.utf-8" in f:
                    path = os.path.join(prefix, *f["path.utf-8"])
                else:
                    path = decode_string(os.path.join(prefix, decode_string(os.path.join(*f["path"]), self.encoding)), self.encoding)
                self.__m_files.append({
                    'path': path,
                    'size': f["length"],
                    'download': True
                })
        else:
            self.__m_files.append({
                "path": self.__m_name,
                "size": self.__m_metadata["info"]["length"],
                "download": True
        })

    def as_dict(self, *keys):
        """
        Return the torrent info as a dictionary, only including the passed in
        keys.

        :param keys: a number of key strings
        :type keys: string
        """
        return dict([(key, getattr(self, key)) for key in keys])

    @property
    def name(self):
        """
        The name of the torrent.

        :rtype: string
        """
        return self.__m_name

    @property
    def info_hash(self):
        """
        The torrents info_hash

        :rtype: string
        """
        return self.__m_info_hash

    @property
    def files(self):
        """
        A list of the files that the torrent contains.

        :rtype: list
        """
        return self.__m_files

    @property
    def files_tree(self):
        """
        A dictionary based tree of the files.

        ::

            {
                "some_directory": {
                    "some_file": (index, size, download)
                }
            }

        :rtype: dictionary
        """
        return self.__m_files_tree

    @property
    def metadata(self):
        """
        The torrents metadata.

        :rtype: dictionary
        """
        return self.__m_metadata

    @property
    def filedata(self):
        """
        The torrents file data.  This will be the bencoded dictionary read
        from the torrent file.

        :rtype: string
        """
        return self.__m_filedata
