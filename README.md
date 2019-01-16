# transmission-trackers
Script to automatically add trackers from a list to all torrents in Transmission.
This allows to get more peers to download/upload from/to.

Features:
* Download lists of trackers from any number of URLs and cache them locally. The cache will only be updated after the specified time passes (e.g. once a day)
* Check if trackers obtained from remote URLs are resolvable in DNS
* Load additional local tracker lists
* Remove duplicates so that only unique hosts and IPs are used: if two or more URLs point to the same hostname or the hostname resolves to the same IP - only one URL will be loaded
* Optionally filter torrents by status (seeding, stopped etc)
* Compare the current tracker list of a torrent with the required one and only update Transmission if they don't match

Tracker list format:
* One tracker URL per line
* Empty lines are ignored
* Only `http[s]://` and `udp://` trackers are loaded (Transmission does not support WebSocket trackers AFAIK)

Requirements:
* Should work with both Python 2.7 and 3.x, although there may be problems with logging in Python2 due to different unicode handling, I don't want to fix that :)
* *transmissionrpc* Python module

Usage:
* Get *transmissionrpc*: ```pip[3] install transmissionrpc``` (or using any other method)
* Put the *transmission-trackers.py* script somewhere
* Make sure that the right Python interpreter is used (it's *python3* by default)
* Adjust the host/port/credentials to access the Transmission RPC inside the script
* Add your URLs and local files to the appropriate lists in the script
* Adjust other parameters if needed (see comments)
* Make the script run by cron e.g. every minute
* You're done
