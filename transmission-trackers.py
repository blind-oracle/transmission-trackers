#!/usr/bin/env python3

import transmissionrpc, sys, os, time

# Host, port, username and password to connect to Transmission
# Set user and pw to None if auth is not required
host, port, user, pw = 'localhost', 9091, 'admin', 'pwd'

# Work with torrents having only these statuses.
# Can be any combination of: 'check pending', 'checking', 'downloading', 'seeding', 'stopped'
# If empty - will affect all torrents
status_filter = ()

# How frequently to update trackers cache
update_freq = 86400

# Path to trackers URL and local cache
trackers_url = 'https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt'
trackers_file = '/tmp/trackers_all.txt'

# Don't print anything (unless an error occures)
silent = False
# Debug output
debug = False

###
if silent: debug = False
trackers = None

def readTrackers():
  f = open(trackers_file, 'r')
  trackers = set(())

  for t in f.readlines():
    t = t.strip()
    if not t.startswith('http') or not t.startswith('udp'):
      continue
    trackers.add(t)

  f.close()
  if debug: print('{} trackers loaded from {}'.format(len(trackers), trackers_file))
  return trackers

def downloadTrackers():
  update = False

  try:
    mt = os.stat(trackers_file).st_mtime
    if time.time() - mt > update_freq:
      update = True
  except:
    update = True

  if not update:
    return

  if sys.version_info[0] == 2:
    import urllib
    urllib.urlretrieve(trackers_url, trackers_file)
  else:
    import urllib.request
    urllib.request.urlretrieve(trackers_url, trackers_file)

  trackers = readTrackers()
  if not silent: print('Trackers list updated ({} loaded)'.format(len(trackers)))

downloadTrackers()
if not trackers: trackers = readTrackers()

tc = transmissionrpc.Client(host, port=port, user=user, password=pw)
torrents = tc.get_torrents()

if debug: print('{} torrents total'.format(len(torrents)))

for t in torrents:
  if status_filter and not t.status in status_filter:
    if debug: print('{}: skipping due to status filter'.format(t.name))
    continue

  ttrk = set(())
  for trk in t.trackers:
    ttrk.add(trk['announce'])

  diff = trackers - ttrk

  if diff:
    if not silent: print('{}: Adding {} trackers (before: {})'.format(t.name, len(diff)), len(ttrk))
    tc.change_torrent(t.id, trackerAdd=list(diff))
  else:
    if debug: print('{}: update not needed'.format(t.name))
