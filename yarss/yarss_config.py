#
# dialog_email_message.py
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

import gtk
import gtk.glade 

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import *

DEFAULT_UPDATE_INTERVAL = 120
DEFAULT_PREFS = {
    "email_configurations": {
        "send_email_on_torrent_events": False,
        "from_address": "",
        "smtp_server": "",
        "smtp_port": "",
        "smtp_authentication": False,
        "smtp_username": "",
        "smtp_password": ""
        },
    "rssfeeds":{},
    "subscriptions":{},
    "cookies":{},
    "email_messages":{}
}


class YARSSConfig(object):

    def __init__(self):
        self.config = deluge.configmanager.ConfigManager("yarss.conf", DEFAULT_PREFS)
        self.verify_config()
        print "Loaded email config:", self.config["email_configurations"]

    def save(self):
        self.config.save()
    
    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    def set_config(self, config):
        """Replaces the config data in self.config with the available keys in config"""
        for key in config.keys():
            self.config[key] = config[key]
            print "setting core config:", key
            if key == "email_configurations":
                print "Email config::", self.config[key]

        print "Saving to file"
        self.config.save()

    def get_new_config_key(self, dictionary):
        """Returns the first unused key that is a integer, as string"""
        key = 0
        while (dictionary.has_key(str(key))):
            key += 1
        return str(key)

    def generic_save_config(self, config_name, dict_key=None, data_dict=None, delete=False):
        """Save email message to config. If dict_key is None, create new key
        If message_dict is None, delete message with key==dict_key
        config_name must be either of the dictionaries in the main config (See DEFAULT_PREFS):
        """
        if data_dict != None and type(data_dict) != dict:
            raise ValueError("generic_save_config: data_dict must be a dictionary: '%s'" % str(data_dict))
        
        if not DEFAULT_PREFS.has_key(config_name):
            raise ValueError("Invalid config key:" + str(config_name))

        config = self.config[config_name]

        # Means delete
        if data_dict == None:
            if dict_key == None:
                raise ValueError("generic_save_config: key and value cannot both be None") 
            if not delete:
                raise ValueError("generic_save_config: deleting item requires 'delete' to be True") 
           # Value is None, means delete entry with key dict_key
            if config.has_key(dict_key):
                del config[dict_key]
                # Save main config to file
                self.config.save()
                return self.config.config
            else:
                raise ValueError("generic_save_config: Invalid key - Item with key %s doesn't exist" % dict_key) 
        else: # Save config
            # The entry to save does not have an item 'key'. This means it's a new entry to the database
            if not data_dict.has_key("key"):
                dict_key = self.get_new_config_key(config)
                data_dict["key"] = dict_key
            else:
                dict_key = data_dict["key"]

        config[dict_key] = data_dict
        self.config.save()
        return self.config.config

    def verify_config(self):
        """Adding missing keys, in case a new version adds more config fields"""
        
        default_config = get_fresh_subscription_config()
        changed = False
        changed = self.insert_missing_values(self.config["subscriptions"], default_config, changed)

        default_config = get_fresh_rssfeed_config()
        changed = self.insert_missing_values(self.config["rssfeeds"], default_config, changed)

        if changed:
            self.config.save()

    def insert_missing_values(self, config, default_config, changed):
        key_diff = None
        for config_key in config.keys():
            item = config[config_key]
            if key_diff == None:
                key_diff = set(default_config.keys()) - set(item.keys())
                # No keys missing, so nothing to do
                if not key_diff:
                    return
                changed = True
            # Set new keys
            for key in key_diff:
                item[key] = default_config[key]

    def new_subscription_config(self, name="", rssfeed_key="", regex_include="", regex_exclude="", 
                                active=True, search=True, move_completed="",
                                last_update=get_default_date().isoformat()):
        """Create a new config (dictionary) for a feed.
        If rssfeed_key does not correspond to a real key, the config cannot be used to save a real subscription"""
        config_dict = get_fresh_subscription_config(name=name, rssfeed_key=rssfeed_key, regex_include=regex_include, regex_exclude=regex_exclude, 
                                                    active=active, search=search, move_completed=move_completed,
                                                    last_update=last_update)
        config_dict["key"] = self.get_new_config_key(self.config["subscriptions"])
        return config_dict

    def new_rssfeed_config(self, name="", url="", site="", active=True, last_update="", 
                           update_interval=DEFAULT_UPDATE_INTERVAL):
        """Create a new config (dictionary) for a feed"""
        config_dict = get_fresh_rssfeed_config(name=name, url=url, site=site, active=active, last_update=last_update, 
                                               update_interval=update_interval)

        config_dict["key"] = self.get_new_config_key(self.config["rssfeeds"])
        return config_dict


####################################
# Can be called from outside core
####################################

def get_fresh_rssfeed_config(name="", url="", site="", active=True, last_update="", 
                       update_interval=DEFAULT_UPDATE_INTERVAL):
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    #config_dict["key"] = self.get_new_config_key(self.config["rssfeeds"])
    config_dict["name"] = name
    config_dict["url"] = url
    config_dict["site"] = site
    config_dict["active"] = active        
    config_dict["last_update"] = last_update
    config_dict["update_interval"] = update_interval
    return config_dict


def get_fresh_subscription_config(name="", rssfeed_key="", regex_include="", regex_exclude="", 
                            active=True, search=True, move_completed="",
                            last_update=get_default_date().isoformat()):
    """Create a new config """
    config_dict = {}
    #config_dict["key"] = self.get_new_config_key(self.config["subscriptions"])
    config_dict["rssfeed_key"] = rssfeed_key
    config_dict["regex_include"] = regex_include
    config_dict["regex_include_ignorecase"] = True
    config_dict["regex_exclude"] = regex_exclude
    config_dict["regex_exclude_ignorecase"] = True
    config_dict["name"] = name
    config_dict["active"] = active
    config_dict["search"] = search
    config_dict["last_update"] = last_update
    config_dict["move_completed"] = move_completed
    config_dict["email_notifications"] = {}
    return config_dict


def get_fresh_message_config():
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["name"] = ""
    config_dict["to_address"] = ""
    config_dict["subject"] = ""
    config_dict["message"] = ""
    config_dict["active"] = True
    return config_dict

def get_fresh_cookie_config():
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["site"] = ""
    config_dict["value"] = []
    config_dict["active"] = True
    return config_dict


#    def save_config(self, subscription_config=None, rssfeed_config=None):
#        """Saves the configs for a subscription and/or a rssfeed"""
#        if subscription_config:
#            self.config["subscriptions"][subscription_config["key"]] = subscription_config
#        if rssfeed_config:
#            from urlparse import urlparse
#            rssfeed_config["site"] = urlparse(rssfeed_config["url"]).netloc
#            self.config["rssfeeds"][rssfeed_config["key"]] = rssfeed_config
#        self.config.save()
#        return self.config.config
#



    # NOT WORKING
    def verify_and_update_config_format(self):
        """Converts the loaded config if it is old"""
        # Contains no feeds
        if len(self.config['abos']) == 0:
            return
        for key in self.config['abos'].keys():
            if type(self.config['abos'][key]) == dict:
                return            
            # Old version 0.1 config list format
            conf = self.config['abos'][key]
            # Delete config with name as key
            del self.config['abos'][key]
            # format of old config is a list with the values: 
            # (distri, url, regex, show, quality, active, search, date)
            log.info("YARSS: Convert old yarss (v0.1) config:" + str(conf))
            new_config = self.new_subscription_config(url=conf[1], regex=conf[2], name=key, 
                                                      quality=conf[4], active=conf[5],
                                                      search=conf[6], date=conf[7])
            log.info("YARSS: Saved as:" + str(new_config))
            self.save_feed_config(new_config)


    
        
