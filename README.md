# transmission-trackers
Script to automatically add trackers from a list to all torrents in Transmission.
This allows to get more peers to download/upload from/to.

Logic:
* Download & cache a list of trackers from a specified URL - currently tested only with [ngosang/trackerslist](https://github.com/ngosang/trackerslist). The cache will only be updated after the specified time passes (e.g. once a day)
* Fetch the tracker list of each torrent in Transmission and add all trackers from a downloaded list to each of the torrents.
* Optionally filter by torrent status (seeding, stopped etc)
* If the tracker list of the torrent is already up-to-date then nothing is done.

Tracker list format:
* One tracker URL per line
* Empty lines are ignored
* Only HTTP(S) and UDP trackers are loaded (Transmission does not support WebSocket trackers AFAIK)

Requirements:
* Should work with both Python 2 and 3, although there may be problems with logging in Python2 due to different unicode handling.
* *transmissionrpc* Python module.

Usage:
* Install *transmissionrpc*: ```pip[3] install transmissionrpc```
* Put the *transmission-trackers.py* script somewhere
* Make sure that the right Python interpreter is used (it's *python3* by default)
* Adjust the host/port/credentials to access the Transmission RPC inside the script
* Make the script run by cron e.g. every minute
* You're done
