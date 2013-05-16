#!/usr/bin/python

import libtorrent as lt
import time
import logging
import threading
import os

#logging.basicConfig(level=DEBUG)
# rescanning package cache every X seconds
# nach einer zeit "stalled" das seeding
# nicht packete hinzufügen, wenn pacman db log aktiv
# systemd service file

ses = lt.session()

class torrent:
	def __init__(self, path, item):
		self.path = path
		self.item = item

		info = lt.torrent_info(path+"/"+item)
		self.h = ses.add_torrent(info, path)
	
	def print_stat(self):
			h = self.h
			s = h.status()
			state_str = ['queued', 'checking', 'downloading metadata', \
				'downloading', 'finished', 'seeding', 'allocating']
			print ('%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
				(s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
				s.num_peers, state_str[s.state]))
		
class threadstart(threading.Thread):
	def __init__(self, path, item):
		threading.Thread.__init__(self)
		self.path = path
		self.item = item
	def run(self):
		#logging.debug('Loading torrent file in thread: '+self.path)
		print("Loading torrent file in thread")
		print(self.path)
		print(self.item)
		package = torrent(self.path, self.item)

def walklevel(some_dir, level):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def scandir(path, level):
	if os.path.exists(path):
		for (path, dirs, files) in walklevel(path,level):
			for item in files:
				if ".torrent" in item:
				    thread = threadstart(path,item)
				    thread.start()
				    time.sleep(1)
	else:
	    print("File or directory does not exists")


state = None
ses.start_dht(state)

ses.add_dht_router("router.bittorrent.com", 6881)
ses.add_dht_router("router.utorrent.com", 6881)
ses.add_dht_router("router.bitcomet.com", 6881)

ses.listen_on(6881, 6891)

scandir("/var/cache/pacman/pkg",1)

while True:
	time.sleep(5)
