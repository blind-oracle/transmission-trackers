#!/usr/bin/env python3

# Host, port, username and password to connect to Transmission
# Set user and pw to None if auth is not required
host, port, user, pw = 'localhost', 9091, 'admin', 'pwd'

# Work with torrents having only these statuses.
# Can be any combination of: 'check pending', 'checking', 'downloading', 'seeding', 'stopped'
# If empty - will affect all torrents
status_filter = ()

# How frequently to update trackers cache
update_freq = 86400

# A list of URLs where to get the tracker lists from.
# The lists are combined into one with duplicates removed.
# The trackers from these lists are checked by looking up the URL's hostname in DNS.
urls = [
  'https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt',
  # 'http://some.other.tracker.list/trackers.txt'
  # ...
]

# Whether to print an error if connection failed (no Transmission running?)
err_on_connect = False

# Where to cache downloaded lists
cache_file = '/tmp/trackers_cache.txt'

# Additional local lists of trackers to load.
# Better to use absolute paths.
# These are not checked against DNS
local_lists = [
  # '/var/cache/trackers1.txt'
  # '/var/cache/trackers2.txt'
  # ...
]

# Don't print anything (unless an error occures)
silent = False
# Debug output
debug = False

### Configuration ends here ###
hdrs = {'User-Agent': 'Mozilla/5.0'}
hosts, ips = set(()), set(())

import transmissionrpc, sys, os, time, socket

if sys.version_info[0] == 2:
  from urllib import Request, urlopen
  from urlparse import urlparse
else:
  from urllib.request import Request, urlopen
  from urllib.parse import urlparse

def lg(msg):
  if not silent: print(msg)

def dbg(msg):
  if debug: lg(msg)

def parse(txt):
  l = []
  for t in txt.split('\n'):
    t = t.strip()
    if t.startswith('http') or t.startswith('udp'):
      l.append(t)
  return l

def validateTrackerURL(url, dns=True):
  try:
    h = urlparse(url).netloc.split(':', 1)[0]
  except:
    lg("Tracker URL '{}' is malformed".format(url))
    return False

  if h in hosts:
    dbg("Host '{}' is duplicate".format(h))
    return False

  ipa = set(())
  if dns:
    try:
      for r in socket.getaddrinfo(h, None):
        ipa.add(r[4][0])
    except:
      lg("Host '{}' is not resolvable".format(h))
      return False

    for ip in ipa:
      if ip in ips:
        dbg("Host's '{}' IP '{}' is duplicate".format(h, ip))
        return False

    ips.add(ip)

  dbg("Approving tracker '{}'".format(url))
  hosts.add(h)
  return True

def loadFile(file):
  f = open(file, 'r')
  l = parse(f.read())
  f.close()
  return l

def loadURL(url):
  req = Request(url, headers=hdrs)
  f = urlopen(req)
  l = parse(f.read().decode("utf-8"))
  f.close()
  return l

def downloadLists():
  update = False

  try:
    mt = os.stat(cache_file).st_mtime
    if time.time() - mt > update_freq:
      update = True
  except:
    update = True

  if not update:
    return None

  trk = []
  for url in urls:
    l = loadURL(url)
    trk += l
    dbg("Remote URL '{}' loaded: {} trackers".format(url, len(l)))

  valid = []
  for t in trk:
    if validateTrackerURL(t): valid.append(t)

  f = open(cache_file, "w+")
  f.write('\n'.join(valid))
  f.close()

  return valid

def readLocalLists():
  trk = []
  for f in local_lists:
    l = loadFile(f)
    trk += l
    dbg("Local list '{}' loaded: {} trackers".format(f, len(l)))

  valid = []
  for t in trk:
    if validateTrackerURL(t, dns=False): valid.append(t)

  return valid

trk_remote = downloadLists()
if trk_remote:
  lg('Remote URLs downloaded: {} trackers'.format(len(trk_remote)))
elif trk_remote is None:
  trk_remote = []
  local_lists.append(cache_file)

trk_local = readLocalLists()
if trk_local:
  dbg('Local lists loaded: {} trackers'.format(len(trk_local)))

trackers = set(trk_remote + trk_local)
dbg('Total trackers: {}'.format(len(trackers)))

if not trackers:
  lg("No trackers loaded, nothing to do")
  exit(1)

try:
  tc = transmissionrpc.Client(host, port=port, user=user, password=pw)
except:
  if not err_on_connect:
    exit()

  print("Unable to connect to Transmission: ", sys.exc_info()[0])
  raise

torrents = tc.get_torrents()

dbg('{} torrents total'.format(len(torrents)))

for t in torrents:
  if status_filter and not t.status in status_filter:
    dbg('{}: skipping due to status filter'.format(t.name))
    continue

  ttrk = set(())
  for trk in t.trackers:
    ttrk.add(trk['announce'])

  diff = trackers - ttrk

  if diff:
    lg('{}: Adding {} trackers (before: {})'.format(t.name, len(diff), len(ttrk)))
    tc.change_torrent(t.id, trackerAdd=list(diff))
  else:
    dbg('{}: update not needed'.format(t.name))
