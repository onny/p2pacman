#!/usr/bin/python
import subprocess
import re
import threading
import requests
import libtorrent as lt
import time
from sys import exit
import os

ses = lt.session()

state = None
ses.start_dht(state)

ses.add_dht_router("router.bittorrent.com", 6881)
ses.add_dht_router("router.utorrent.com", 6881)
ses.add_dht_router("router.bitcomet.com", 6881)

ses.listen_on(6881, 6891)

# properly remove object
# verbose flag for additional information
# pacman like usage: python-progressbar
# p2p packet list
# torrent timout and then use normal dl

packages = []

class torrent:          
        def __init__(self, path):
                self.path = path
                                
                info = lt.torrent_info(path)
                self.h = ses.add_torrent(info, "/var/cache/pacman/pkg/")

        def return_state(self):
            if self.h.status().state != lt.torrent_status.seeding:
                return 1
            else:
                return 0

        def print_state(self):
            h = self.h
#                        while (h.status().state != lt.torrent_status.seeding):
            s = h.status()
            state_str = ['queued', 'checking', 'downloading metadata', \
                         'downloading', 'finished', 'seeding', 'allocating']

            packagename = self.path.split('/')[-1].replace('.torrent','')
            print (' - '+packagename + ': %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d)' % \
                    (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
                    s.num_peers))
                    #s.num_peers, state_str[s.state]))
                
class threadstart(threading.Thread):
        def __init__(self, path):
                threading.Thread.__init__(self)
                self.path = path
        def run(self):
                #logging.debug('Loading torrent file in thread: '+self.path)
                print("Loading torrent file in thread")
                package = torrent(self.path)
                packages.append(package)

print("syncing pacman database ...")
process = subprocess.Popen(['pacman', '-Syup'], shell=False, stdout=subprocess.PIPE)
processret = str(process.communicate()[0])                          # get python stdout
processret = processret.replace("pkg.tar.xz","pkg.tar.xz.torrent")  # append to every link .torrent

matchObject = re.search(r'(http://.*.pkg.tar.xz.torrent)', processret)      # match all links
if matchObject:
    torrentlinks = matchObject.group(1).split("\\n")                        # split links into a tuple
else:
    print("no updates available")
    exit(0)

print("downloading torrent metadata ...")
for link in torrentlinks:
    try:
        r = requests.get(link)
    except:
        print("error: mirror refues the connection, aborting.")
        exit(1)
    if r.status_code == 200:
        with open("/var/cache/pacman/pkg/"+link.split('/')[-1], 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)
            f.close
    else:
        print("error: your mirror doesn't have proper torrent support")
        exit(1)
    thread = threadstart("/var/cache/pacman/pkg/"+link.split('/')[-1])
    thread.start()
    time.sleep(5)

print("starting torrents ...")
while len(packages):
    print("downloading "+str(len(packages))+" package(s):")
    for torrent in packages:
        torrent.print_state()
        if not torrent.return_state():
            packages.pop(-1)
    time.sleep(5)

print("all downloads finished!")
print("installing packages ...")

links = ""
for n, torrentlink in enumerate(torrentlinks):
    links += "/var/cache/pacman/pkg/"+torrentlink.split('/')[-1].replace('.torrent','')+" "
os.system("pacman -U "+links)
