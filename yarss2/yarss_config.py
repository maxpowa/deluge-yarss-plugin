# -*- coding: utf-8 -*-
#
# yarss_config.py
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

import deluge.configmanager
from deluge.event import DelugeEvent
import copy
from yarss2 import common

DEFAULT_UPDATE_INTERVAL = 120

DUMMY_RSSFEED_KEY = "9999"

__DEFAULT_PREFS = {
    "email_configurations": {},
    "rssfeeds": {},
    "subscriptions": {},
    "cookies": {},
    "email_messages": {}
    }

def default_prefs():
    return copy.deepcopy(__DEFAULT_PREFS)

class YARSSConfigChangedEvent(DelugeEvent):
    """
    Emitted when the config has been changed.
    """
    def __init__(self, config):
        """
        :param config: the new config
        """
        self._args = [config]

class YARSSConfig(object):

    def __init__(self, logger, config=None):
        self.log = logger
        # Used for testing
        if config is not None:
            self.config = config
        else:
            self.config = deluge.configmanager.ConfigManager("yarss2.conf", default_prefs())
            self._verify_config()

    def save(self):
        self.config.save()

    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    def set_config(self, config):
        """Replaces the config data in self.config with the available keys in config"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    def generic_save_config(self, config_name, dict_key=None, data_dict=None, delete=False):
        """Save email message to config.

        If data_dict is None, delete message with key==dict_key
        If data_dict is not None, dict_key is ignored
        If data_dict does not have a key named "key", it's a new config element, so a new key is created.

        config_name must be either of the dictionaries in the main config (See DEFAULT_PREFS):
        """
        if data_dict is not None and type(data_dict) != dict:
            raise ValueError("generic_save_config: data_dict must be a dictionary: '%s'" % str(data_dict))

        if not default_prefs().has_key(config_name):
            raise ValueError("Invalid config key:" + str(config_name))

        config = self.config[config_name]

        # Means delete
        if data_dict is None:
            if dict_key is None:
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
                raise ValueError("generic_save_config: Invalid key - "\
                                     "Item with key %s doesn't exist" % dict_key)
        else: # Save config
            # The entry to save does not have an item 'key'. This means it's a new entry in the config
            if not data_dict.has_key("key"):
                dict_key = common.get_new_dict_key(config)
                data_dict["key"] = dict_key
            else:
                dict_key = data_dict["key"]

        config[dict_key] = data_dict
        self.config.save()
        return self.config.config

    def _verify_config(self):
        """Adding missing keys, in case a new version adds more config fields"""
        default_config = get_fresh_subscription_config(key="")
        changed = False

        if self._insert_missing_dict_values(self.config["subscriptions"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["subscriptions"], default_config):
            changed = True

        default_config = get_fresh_rssfeed_config()
        if self._insert_missing_dict_values(self.config["rssfeeds"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["rssfeeds"], default_config):
            changed = True

        default_config = get_fresh_message_config()
        if self._insert_missing_dict_values(self.config["email_messages"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["email_messages"], default_config):
            changed = True

        default_config = get_fresh_email_configurations()
        if self._insert_missing_dict_values(self.config["email_configurations"], default_config, level=1):
            changed = True
        if self._verify_types(None, self.config["email_configurations"], default_config):
            changed = True

        if changed:
            self.config.save()

    def _verify_types_config_elements(self, config_dict, default_config):
        """Takes a dictinoary and calls _verify_types with each element
        (which is also a dictionary)"""
        changed = False
        for key in config_dict.keys():
            if self._verify_types(key, config_dict[key], default_config):
                changed = True
                # Elements have been removed, so remove from config
                if len(config_dict[key].keys()) == 0:
                    del config_dict[key]
        return changed

    def _verify_types(self, config_key, config, default_config):
        """Takes a dictinoary and checks each key/value pair"""
        changed = False
        for key in default_config.keys():
            rssfeed_key_invalid = False
            if not config.has_key(key):
                # We have a problem. Cannot use the default value for a key
                if key == "key":
                    # The key value is missing, so reinsert it.
                    config[key] = config_key
                    changed = True
                elif key == "rssfeed_key":
                    # Cannot insert default value, and cannot know the correct value.
                    rssfeed_key_invalid = True
                else:
                    self.log.warn("Config is missing a dictionary key: '%s'. Inserting "\
                                  "default value ('%s'). Affected config: %s\n" %
                                  (key, str(default_config[key]), str(config)))
                    config[key] = default_config[key]
                changed = True
            else:
                if type(default_config[key]) != type(config[key]):
                    if key == "key":
                        config[key] = config_key
                        changed = True
                    # We have a problem
                    elif key == "rssfeed_key":
                        if type(config[key]) is unicode:
                            try:
                                # Verify it's an integer
                                int(config[key])
                                config[key] = str(config[key])
                            except ValueError:
                                rssfeed_key_invalid = True
                        else:
                            rssfeed_key_invalid = True
                            self.log.warn("The value of the dictionary key '%s' has the wrong type! Value: '%s'."\
                                          "Excpected '%s' but found '%s'. Must be fixed manually."\
                                          "\nAffected config: %s\n" % (key,  str(type(default_config[key])),
                                                                       str(type(config[key])), str(config[key]), str(config)))
                    # If default is unicode, and value is str
                    elif (type(default_config[key]) is unicode and type(config[key]) is str):
                        # Ignore if default is unicode and value is an empty string,
                        # (No point in replacing empty unicode string with ascii string)
                        if config[key] != "":
                            # Try to convert to unicode
                            try:
                                config[key] = config[key].decode("utf8")
                            except:
                                config[key] = default_config[key]
                            changed = True
                    else:
                        self.log.warn("Config value ('%s') is the wrong data type! dictionary key: '%s'. "\
                                 "Expected '%s' but found '%s'. Inserting default value. Affected config: %s" % \
                                 (config[key], key, str(type(default_config[key])), str(type(config[key])), str(config)))
                        config[key] = default_config[key]
                        changed = True
                # Test if key and rssfeed_key are valid
                if key == "key" or (key == "rssfeed_key" and not rssfeed_key_invalid):
                    # Test that they are numbers
                    if not config[key].isdigit():
                        # Replace with config_key
                        if key == "key":
                            config[key] = config_key
                            changed = True
                            # We have a problem
                        else:
                            #print "rssfeed_dict_key not integer: '%s'" % config[key]
                            rssfeed_key_invalid = True
                    else:
                        # Test that rssfeed_key points to a rssfeed that exists in the config
                        if key == "rssfeed_key":
                            # The rsfeed_key is invalid (no rssfeed with that key exists)
                            if not self.config["rssfeeds"].has_key(config[key]):
                                print "\n\nRSSFEED DOES NOT EXIST\n\n"
                                rssfeed_key_invalid = True
            # Must handle missing rssfeed_key in a subscription
            if rssfeed_key_invalid:
                # Check first if the subscription has the default values. In that case, just delete it.
                # If it has the key 'key', use that as key, else None
                default_config = get_fresh_subscription_config(key=None if not config.has_key("key") else config["key"],
                                                               rssfeed_key=None if not config.has_key("rssfeed_key") else config["rssfeed_key"])
                if common.dicts_equals(config, default_config):
                    self.log.warn("Found subscription with missing rssfeed_key. The subscription is empty, so it will be deleted.")
                    for key in config.keys():
                        del config[key]
                    return True
                else:
                    # The subscription has non-default values. Use a dummy rssfeed
                    if self.config["rssfeeds"].has_key(DUMMY_RSSFEED_KEY):
                        dummy_rssfeed = self.config["rssfeeds"][DUMMY_RSSFEED_KEY]
                    else:
                        dummy_rssfeed = get_fresh_rssfeed_config(name=u"Dummy Feed (error in config was detected)", active=False, key=DUMMY_RSSFEED_KEY)
                        self.config["rssfeeds"][DUMMY_RSSFEED_KEY] = dummy_rssfeed
                    config["rssfeed_key"] = DUMMY_RSSFEED_KEY
                    self.log.warn("Found subscription with missing rssfeed_key. A dummy rssfeed was created for this subscription.")
        return changed

    def _insert_missing_dict_values(self, config_dict, default_config, key_diff=None, level=2):
        if level == 1:
            return self._do_insert(config_dict, default_config, key_diff)
        else:
            level = level - 1
            for key in config_dict.keys():
                key_diff = self._insert_missing_dict_values(config_dict[key], default_config,
                                                      key_diff=key_diff, level=level)
                if not key_diff:
                    return key_diff
        return key_diff

    def _do_insert(self, config_dict, default_config, key_diff):
        if key_diff is None:
            key_diff = set(default_config.keys()) - set(config_dict.keys())
            # No keys missing, so nothing to do
            if not key_diff:
                return key_diff
        # Set new keys
        for key in key_diff:
            self.log.info("Insert missing config key '%s'" % key)
            config_dict[key] = default_config[key]
        return key_diff


####################################
# Can be called from outside core
####################################

def get_fresh_email_configurations():
    """Return the default email_configurations dictionary"""
    config_dict = {}
    config_dict["send_email_on_torrent_events"] = False
    config_dict["from_address"] = u""
    config_dict["smtp_server"] = u""
    config_dict["smtp_port"] = u""
    config_dict["smtp_authentication"] = False
    config_dict["smtp_username"] = u""
    config_dict["smtp_password"] = u""
    config_dict["default_email_to_address"] = u""
    config_dict["default_email_subject"] = u"[YaRSS2]: RSS event"
    config_dict["default_email_message"] = u"""Hi

The following torrents have been downloaded:

$torrentlist

Regards
"""
    return config_dict

def get_fresh_rssfeed_config(name=u"", url=u"", site=u"", active=True, last_update=u"",
                             update_interval=DEFAULT_UPDATE_INTERVAL, obey_ttl=False, key=None):
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["name"] = name
    config_dict["url"] = url
    config_dict["site"] = site
    config_dict["active"] = active
    config_dict["last_update"] = last_update
    config_dict["update_interval"] = update_interval
    config_dict["obey_ttl"] = obey_ttl
    if key:
        config_dict["key"] = key
    return config_dict

def get_fresh_subscription_config(name=u"", rssfeed_key="", regex_include=u"", regex_exclude=u"",
                                  active=True, move_completed=u"", download_location=u"", last_update=u"", key=None):
    """Create a new config """
    config_dict = {}
    config_dict["rssfeed_key"] = rssfeed_key
    config_dict["regex_include"] = regex_include
    config_dict["regex_include_ignorecase"] = True
    config_dict["regex_exclude"] = regex_exclude
    config_dict["regex_exclude_ignorecase"] = True
    config_dict["name"] = name
    config_dict["active"] = active
    config_dict["last_update"] = last_update
    config_dict["move_completed"] = move_completed
    config_dict["download_location"] = download_location
    config_dict["custom_text_lines"] = u""
    config_dict["add_torrents_in_paused_state"] = False
    config_dict["email_notifications"] = {} # Dictionary where keys are the keys of email_messages dictionary
    if key is not None:
        config_dict["key"] = key
    return config_dict

def get_fresh_message_config():
    """Create a new config (dictionary) for a email message"""
    config_dict = {}
    config_dict["name"] = u""
    config_dict["to_address"] = u""
    config_dict["subject"] = u""
    config_dict["message"] = u""
    config_dict["active"] = True
    return config_dict

def get_fresh_cookie_config():
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["site"] = u""
    config_dict["value"] = []
    config_dict["active"] = True
    return config_dict
