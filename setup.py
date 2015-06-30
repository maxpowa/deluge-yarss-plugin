# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 bendikro bro.devel+yarss2@gmail.com
#
# Based on work by:
# Copyright (C) 2009 Camillo Dell'mour <cdellmour@gmail.com>
#
# This file is part of YaRSS2 and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import setup, find_packages

__plugin_name__ = "YaRSS2"
__author__ = "Bro"
__author_email__ = "bro.devel+yarss2@gmail.com"
__version__ = "1.3.3"
__url__ = "http://dev.deluge-torrent.org/wiki/Plugins/YaRSS2"
__license__ = "GPLv3"
__description__ = "Yet another RSS 2"
__long_description__ = """
Yet another RSS 2, a simple RSS plugin for Deluge, based on
YaRSS written by Camillo Dell'mour <cdellmour@gmail.com>.
Last updated on 2014-7-25, tested with Deluge 1.3.7.
Requires PyGTK 2.24
"""

__pkg_data__ = {__plugin_name__.lower(): ["data/*"]}
packages = find_packages(exclude=["yarss2.tests"])

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,
    packages=packages,
    package_data = __pkg_data__,
    entry_points="""
    [deluge.plugin.core]
    %s = %s:CorePlugin
    [deluge.plugin.gtkui]
    %s = %s:GtkUIPlugin
    [yarss2.libpaths]
    include = yarss2.include
    """ % ((__plugin_name__, __plugin_name__.lower())*2)
)
