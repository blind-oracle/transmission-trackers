#!/usr/bin/env python3
from __future__ import print_function

# Host, port, username and password to connect to Transmission
# Set user and pw to None if auth is not required
client = {
  'host': 'localhost',
  'port': 9091,
  'user': 'admin',
  'password': 'passwd'
}
config = {

  # Work with torrents having only these statuses.
  # Can be any combination of: 'check pending', 'checking', 'downloading', 'seeding', 'stopped'
  # If empty - will affect all torrents
  'status_filter': (),

  # A list of URLs where to get the tracker lists from.
  # The lists are combined into one with duplicates removed.
  # The trackers from these lists are checked by looking up the URL's hostname in DNS.
  'remote_lists': [
    'https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt',
    'https://raw.githubusercontent.com/zcq100/transmission-trackers/master/tracker_ipv6.txt',
    # ...
  ],

  # How frequently to update trackers cache
  'update_freq': 86400,

  # Additional local lists of trackers to load.
  # Better to use absolute paths.
  # These are not checked against DNS
  'local_lists': [
    # '/var/cache/trackers1.txt'
    # '/var/cache/trackers2.txt'
    # ...
  ],

  # Whether to print an error if connection failed (no Transmission running?)
  'err_on_connect': False,

  # Don't print anything (unless an error occures)
  'silent': False,

  # Debug output
  'debug': False
}
cache_file=None # Universal scope to be set later
from os import getcwd
if getcwd() != '/docker/transmission/transmission-trackers':
  from os import environ as env, path, mkdir
  try:
    import toml
    configfile = path.join( \
      env.get('XDG_CONFIG_HOME', path.join(env.get('HOME',env.get('USERPROFILE',env.get('HOMEPATH',None))),'.config')),
      'transmission/trackers.toml'
    )
    if path.exists(configfile):
      with open(configfile, 'r') as f:
        client, config = toml.load(f).values()
    else:
      if not path.isdir(path.dirname(configfile)):
        mkdir(path.dirname(configfile))
      with open(configfile, 'w') as f:
        toml.dump( {'client': client, 'config': config }, f )
  except KeyError:
  # Where to cache downloaded lists
    cache_file = path.join(env['TEMP'] ,'.cache/trackers.txt')    
else:
  cache_file = '/tmp/trackers_cache.txt'



### Configuration ends here ###
hdrs = {'User-Agent': 'Mozilla/5.0'}
hosts, ips = set(()), set(())

import sys, os, time, socket
try:
  from transmissionrpc import Client
  if 'host' in client:
    client['address'] = client['host']
    del client['host']
except ImportError:
  try:
    from transmission_rpc import Client
    if 'user' in client:
      client['username'] = client['user']
      del client['user']
  except ImportError:
    print("neither transmissionrpc nor transmission-rpc is installed")
    exit()

if sys.version_info[0] == 2:
  from urllib2 import Request, urlopen
  from urlparse import urlparse
else:
  from urllib.request import Request, urlopen
  from urllib.parse import urlparse

def lg(msg):
  if not config['silent']: print(msg)

def dbg(msg):
  if config['debug']: lg(msg)

def parse(txt):
  l = []
  for t in txt.split('\n'):
    t = t.strip()
    if t.startswith('http') or t.startswith('udp'):
      l.append(t)
  return l

def validateTrackerURL(url, dns=True):
  try:
    h = ':'.join(urlparse(url).netloc.split(':')[0:-1])
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
    if time.time() - mt > config['update_freq']:
      update = True
  except:
    update = True

  if not update:
    return None

  trk = []
  for url in config['remote_lists']:
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
  for f in config['local_lists']:
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
  config['local_lists'].append(cache_file)

trk_local = readLocalLists()
if trk_local:
  dbg('Local lists loaded: {} trackers'.format(len(trk_local)))

trackers = set(trk_remote + trk_local)
dbg('Total trackers: {}'.format(len(trackers)))

if not trackers:
  lg("No trackers loaded, nothing to do")
  exit(1)

try:
  tc = Client(**client)
except:
  if not config['err_on_connect']:
    exit()

  print("Unable to connect to Transmission: ", sys.exc_info()[0])
  raise

torrents = tc.get_torrents()

dbg('{} torrents total'.format(len(torrents)))

for t in torrents:
  if config['status_filter'] and not t.status in config['status_filter']:
    dbg('{}: skipping due to status filter'.format(t.name))
    continue
  if t.isPrivate:
    dbg('{}: skipping private torrent'.format(t.name))
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
