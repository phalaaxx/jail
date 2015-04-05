import os
import ctypes
import pwd
import grp
from sys import stdout

from fpm import ConfigureAll


# this is used to access syscalls
libc = ctypes.CDLL('libc.so.6')

# mount options
MS_BIND = 4096

# list of jail mount points
MountPoints = (
	('proc',                    '/jail/root/{0}/proc',                   'proc', 0,       'hidepid=2'),
	('/dev',                    '/jail/root/{0}/dev',                    None,   MS_BIND, None),
	('/dev/pts',                '/jail/root/{0}/dev/pts',                None,   MS_BIND, None),
	('/jail/home/{0}',          '/jail/root/{0}/home/{0}',               None,   MS_BIND, None),
	('/jail/home/{0}',          '/home/{0}',                             None,   MS_BIND, None),
	('/run/mysqld/mysqld.sock', '/jail/root/{0}/run/mysqld/mysqld.sock', None,   MS_BIND, None),
)

# load list of mounted users
um_raw = map(lambda x: x.split(' ')[1].split('/'), open('/proc/mounts').readlines())
UserMounts = set([x[3] for x in um_raw if len(x) == 5 and x[2] == 'root' and x[4] == 'proc'])


# do a bind mount
def doMount(username, group='jail'):
	if username not in grp.getgrnam(group).gr_mem:
		raise 'User not in group %s' % group
	if pwd.getpwnam(username) and username not in UserMounts:
		for source, target, fstype, flags, options in MountPoints:
			libc.mount(
				source.format(username),
				target.format(username),
				fstype,
				flags,
				options)
		UserMounts.add(username)
		return True
	return False


# mount user and configure fpm
def Mount(username, group='jail'):
	ret = doMount(username, group)
	ConfigureAll(UserMounts, group)
	return ret


# mount all jail users
def MountAll(group='jail'):
	users = set(grp.getgrnam(group).gr_mem).difference(UserMounts)
	for i, user in zip(range(len(users)), users):
		print '\r[ {0:5d}/{1:5d} ] Mount({2})'.format(
			i+1,
			len(users),
			user),
		stdout.flush()
		doMount(user, group)
	ConfigureAll(UserMounts, group)
	print


# detach umount a target
def doUmount(username, group='jail'):
	if username not in grp.getgrnam(group).gr_mem:
		raise 'User not in group %s' % group
	if username in UserMounts:
		for _, target, _, _, _ in MountPoints:
			libc.umount2(target.format(username), 2)
		UserMounts.remove(username)
		return True
	return False


# umount user and configure fpm
def Umount(username, group='jail'):
	ret = doUmount(username, group)
	ConfigureAll(UserMounts, group)
	return ret


# umount all jail users
def UmountAll(group='jail'):
	users = set(grp.getgrnam(group).gr_mem).intersection(UserMounts)
	for i, user in zip(range(len(users)), users):
		print '\r[ {0:5d}/{1:5d} ] Umount({2})'.format(
			i+1,
			len(users),
			user),
		stdout.flush()
		doUmount(user, group)
	ConfigureAll(UserMounts, group)
	print


# list all mounted users
def List(f=lambda x: True):
	return filter(f, UserMounts)
