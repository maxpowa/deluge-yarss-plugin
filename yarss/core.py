#
# core.py
#
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
from deluge._libtorrent import lt
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import feedparser
import re
from twisted.internet.task import LoopingCall
import urllib
import datetime

DEFAULT_PREFS = {
    "updatetime": 120,
    "abos":{}
}

class Core(CorePluginBase):

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("yarss.conf", DEFAULT_PREFS)
        self.verify_and_update_config_format()
        self.update_status_timer = LoopingCall(self.update_handler)
        self.update_status_timer.start(self.config['updatetime'] * 60) # Multiply to get seconds
        
    def disable(self):
        self.update_status_timer.stop()
        self.config.save();

    def update(self):
        pass

    @export
    def set_config(self, config):
        """sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    def add_torrent(self, url, feed_config):
        import os
        basename = os.path.basename(url)

        def download_torrent_file(url):
            import urllib
            webFile = urllib.urlopen(url)
            filedump = webFile.read()
            # Get the info to see if any exceptions are raised
            #info = lt.torrent_info(lt.bdecode(filedump))
            return filedump

        filedump = download_torrent_file(url)
        options={}
        
        if len(feed_config["move_completed"].strip()) > 0:
            options["move_completed"] = True
            options["move_completed_path"] = feed_config["move_completed"].strip()
        torrent_id = component.get("TorrentManager").add(filedump=filedump, filename=basename, options=options)

    @export
    def add_eztv_abo(self, show, quality, name=None):
        url = "http://ezrss.it/search/index.php?show_name=%s&quality=%s&quality_exact=true&mode=simple&mode=rss" % (urllib.quote_plus(show), urllib.quote_plus(quality))
        log.info("YARSS: Url: %s added", url)
        if name is None:
            name = show
        date = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0).isoformat()
        new_config = self.new_feed_config(site="EZTV", url=url, regex=show, name=name, quality=quality, date=date)
        self.config["abos"][new_config["key"]] = new_config
        self.config.save()
        return self.config.config
    
    @export
    def add_feed(self, url, regex, name, move_completed):
        #"format of config name = (distri,url,regex,show,quality,active,search())"
        log.info("YARSS: Url: %s added", url)
        date = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0).isoformat()
        new_config = self.new_feed_config(name=name, url=url, regex=regex, date=date, 
                                          move_completed=move_completed)
        self.save_feed_config(new_config)
        return self.config.config

    @export
    def save_feed(self, feed_config):
        self.save_feed_config(feed_config)
        return self.config.config

    def save_feed_config(self, feed_config):
        from urlparse import urlparse
        feed_config["site"] = urlparse(feed_config["url"]).netloc
        self.config["abos"][feed_config["key"]] = feed_config
        self.config.save()
        return self.config.config

    @export
    def remove_feed(self, key):
        del self.config["abos"][key]
        self.config.save()
        return self.config.config

    @export
    def refresh(self,updatetime = 0):
        """Not Used?"""
        self.update_status_timer.stop()
        if updatetime == 0:
            self.update_status_timer.start(self.config['updatetime'])
        else:
            self.update_status_timer.start(updatetime)
    @export
    def disable_feed(self, key):
        if self.config["abos"].has_key(key):
            log.info("YARSS: Disable_feed: %s", self.config["abos"][key]["name"])
            self.config["abos"][key]["active"] = False
            self.config.save()

    @export 
    def enable_feed(self, key):
        if self.config["abos"].has_key(key):
            log.info("YARSS: Enable_feed: %s", self.config["abos"][key]["name"])
            self.config["abos"][key]["active"] = True
            self.config.save()

    @export
    def run_feed_test(self):
        """Runs the update handler"""
        log.info("YARSS: Running feed test")
        self.update_handler()

    def update_handler(self):
        """Goes through all the feeds and runs the active ones."""
        log.info("YARSS: Update handler executed")
        self.rss_cache = {}
        for key in self.config["abos"].keys():
            config = self.config["abos"][key]
            if config["active"] == True:
                self.fetch_feed(config)
        self.rss_cache = {}

    def fetch_feed(self, feed_config):
        """Search a feed with config 'feed_config'"""
        log.info("YARSS: Fetch feed:" + feed_config["name"])
        if self.rss_cache.has_key(feed_config["url"]):
            d = self.rss_cache[feed_config["url"]]
        else:
            d = feedparser.parse(feed_config["url"])
            self.rss_cache[feed_config["url"]] = d
        p = re.compile(feed_config["regex"])
        try:
            newdate = datetime.datetime.strptime(feed_config["date"], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            newdate = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
        tmpdate = newdate

        # Go through each feed item
        for i in d['items']:
            search_string = i['title']
            log.info("YARSS: Searching feed string:" + search_string)

            if feed_config["search"] == True:
                m = p.search(search_string)
            else:
                m = p.match(search_string)
            if m:
                if newdate < datetime.datetime(*i.date_parsed[:6]):
                    log.info("YARSS: Adding torrent:" + str( i['link']))
                    self.add_torrent(i['link'], feed_config)
                else:
                    log.info("YARSS: Not adding, old timestamp:" + str(search_string))
        for i in d['items']:
            dt = datetime.datetime(*i.date_parsed[:6])
            if tmpdate < dt:
                tmpdate = dt
        feed_config["date"] = tmpdate.isoformat()

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
            # format of old config is a list with the values: (distri, url, regex, show, quality, active, search, date)
            log.info("YARSS: Convert old yarss (v0.1) config:" + str(conf))
            new_config = self.new_feed_config(url=conf[1], regex=conf[2], name=key, 
                                              quality=conf[4], active=conf[5],
                                              search=conf[6], date=conf[7])
            log.info("YARSS: Saved as:" + str(new_config))
            self.save_feed_config(new_config)

    def new_feed_config(self, name="", site="", url="", regex="", quality="", active=True, 
                        search=True, date=None, move_completed=""):
        """Create a new config (dictionary) for a feed"""
        if date == None:
            date = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0).isoformat()
        # Find a new key
        key = 1
        while (self.config["abos"].has_key(str(key))):
            key += 1
        config_dict = {}
        config_dict["key"] = str(key)
        config_dict["site"] = site
        config_dict["url"] = url
        config_dict["regex"] = regex
        config_dict["name"] = name
        config_dict["quality"] = quality
        config_dict["active"] = active
        config_dict["search"] = search
        config_dict["date"] = date
        config_dict["move_completed"] = move_completed
        return config_dict
