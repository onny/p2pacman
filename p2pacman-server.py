#!/usr/bin/python
# dependencies: yaourt -S python-libtorrent-rasterbar rsync mktorrent

# todo:
# - use mktorrent to create torrent files
# - create dns records for:
# 	mirror.project-insanity.org
# 	tracker.project-insanity.org
import os
import libtorrent as lt
import re
import subprocess

mirror = "rsync://ftp.uni-kl.de/pub/linux/archlinux/"
path = "/var/www/mirror.project-insanity.org"
announce = "http://tracker.project-insanity.org:6969/announce"
webseed = ""


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
	torrent = 0
	if os.path.exists(path):
		for (path, dirs, files) in walklevel(path,level):
			for item in files:
				# if pacman package
				if re.search(r'.pkg.tar.xz$', item):
					# create torrent file for package if it doesn't already exist
					if not os.path.isfile(path+"/"+item+".torrent"):
						with open(os.devnull, 'wb') as devnull:
							subprocess.check_call('/usr/bin/mktorrent -a '+announce+' -o '+path+'/'+item+'.torrent '+path+'/'+item, shell=True, stdout=devnull, stderr=subprocess.STDOUT)
						# get torrent info hash and append it to opentracker whitelist
						info = lt.torrent_info(path+"/"+item+".torrent")
						info_hash = info.info_hash()
						hexadecimal = str(info_hash)
						os.system("echo "+hexadecimal+" >> /etc/opentracker/whitelist")
						torrent+=1
				# if torrent file
				if re.search(r'.pkg.tar.xz.torrent$', item):
					# remove torrent file if the inherent package doesn't exist anymore
					if not os.path.isfile(path+"/"+item):
						os.system("rm "+path+"/"+item+".torrent")
					else:
						# get torrent info hash and append it to opentracker whitelist
						info = lt.torrent_info(path+"/"+item)
						info_hash = info.info_hash()
						hexadecimal = str(info_hash)
						os.system("echo "+hexadecimal+" >> /etc/opentracker/whitelist")
					torrent+=1
	else:
	    print("File or directory does not exists")
	return torrent

print("Mirroring ArchLinux repository ...")
os.system("rsync -rptl --delete-after --delay-updates "+mirror+" "+path)
print("Generating torrent files and storing info hashes ...")
os.system("rm /etc/opentracker/whitelist")
torrent = scandir(path,15)
print("Generated "+str(torrent)+" torrent files in X seconds")
print("Reloading opentracker whitelist ...")
os.system("kill -s HUP `pidof opentracker`") # reload whitelist
print('All jobs finished ... quitting')
