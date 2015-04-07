from subprocess import call
from os.path import exists
from os.path import isdir
from os.path import join
from os import makedirs
from os import chown
from os import unlink
from pwd import getpwnam
from grp import getgrnam


uwsgiTemplate = '''# /etc/uwsgi/vassals/{user}.ini
[uwsgi]

plugins = php
socket = /run/uwsgi/app/php-uwsgi.sock
uid = {user}
gid = {user}
chroot = /jail/root/{user}
chdir = /home/{user}/public_html
processes = {processes}
threads = {threads}
enable-threads = true
'''


# get the name of user's php uwsgi file
uwsgiFile = lambda user: join('/etc/uwsgi-emperor/vassals', '%s.ini' % user)

# create uwsgi configuration file for user specified
def uwsgiConfigureUser(User, Processes=6, Threads=15):
	uwsgiConfDir = join('/jail/root', User, 'run/uwsgi/app')
	if not isdir(uwsgiConfDir):
		pw = getpwnam(User)
		makedirs(uwsgiConfDir)
		chown(uwsgiConfDir, pw.pw_uid, pw.pw_gid)

	if not exists(uwsgiFile(User)):
		with open(uwsgiFile(User), 'w+') as fh:
			fh.write(
				uwsgiTemplate.format(
					user       = User,
					processes  = Processes,
					threads    = Threads))


# remove uwsgi user file
def uwsgiDeconfigureUser(User):
	if exists(uwsgiFile(User)):
		unlink(uwsgiFile(User))


# configure all user uwsgi php environments
def uwsgiConfigureAll(UserMounts, group='jail'):
	for user in getgrnam(group).gr_mem:
		if user in UserMounts:
			uwsgiConfigureUser(user)
		else:
			uwsgiDeconfigureUser(user)
