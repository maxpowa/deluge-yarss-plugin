YaRSS2: Yet another RSS 2, a RSS plugin for Deluge.

Author: Bro <bro.development@gmail.com>

Based on YaRSS by Camillo Dell'mour

License: GPLv3

Changelog
=============

v1.1.1 - 2012-10-03

* Fixed import error when running YaRSS2 on daemon without gtk installed.
* feedparser library was unable to parse some timestamps.
* The order of the torrents in the torrent list in the subscription dialog was incorrect.

v1.1.0 - 2012-09-12

* Added panel for log messages.
* Added functionality to reset the last matched timestamp for subscriptions. (Options tab in subscription dialog)
* Fixed bug where RSS feeds with no proper tag for the timestamp when the torrent was published would crash YaRSS2.
* Fixed bug where the 'Published' column in matching panel for subscriptions wasn't properly populated.
* Hopefully fixed bug in GUI that could result in Deluge crashing.

v1.0.4 - 2012-06-27

* Added support for magnet links.
* Running RSS feed fetches in separate thread to avoid having the deluge daemon being busy for too long.
* Added option "Obey TTL" in RSS Feed dialog. With this checked the "Update Interval" will be updated with the TTL value of the RSS Feed.
* Added option "Download location" in subscription dialog.
* Fixed bug where it was possible to delete an email message used by subscriptions for notifications.

v1.0.3 - 2012-05-17

* When adding a RSS Feed or changing the RSS Feed update interval the RSS Feed is now properly (re)schedules with the (new) update interval.
  (Previously a restart of deluge was required)
* After deleting a RSS Feed it is properly stopped from running.
* Added timeout for 10 seconds on feedparser so deluge won't hang in case the server doesn't respond properly.
* "Last update" field in RSS Feeds is now updated properly.
* Added "Last matched" field in Subscriptions list with the timestamp for when the subscription last matched a torrent.
* No longer allow deleting RSS Feeds with subscriptions registered.
* Fixed issue in feedparser where '&' in torrent URLs was converted to &amp.

v1.0.2 - 2012-04-07

* Added mime modules for sending email (required on Windows).

v1.0.1 - 2012-04-01

* Unicode characers can now be used to search.
* Added tests to test some of the most important functionality

v1.0 - 2012-03-27

* First release

(Tested with Deluge 1.3.5)

Tests
============
The directory containing yarss2 must be on the PYTHONPATH

e.g.
yarss2$ export PYTHONPATH=$PYTHONPATH:$PWD/..

Run tests:
yarss2$ trial tests


