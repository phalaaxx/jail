import os
import ctypes
import pwd
import grp


# this is used to access syscalls
libc = ctypes.CDLL('libc.so.6')

# mount options
MS_BIND = 4096

# list of jail mount points
MountPoints = (
	('proc',                        '/jail/root/{0}/proc',                   'proc', 0,       'hidepid=2'),
	('/dev',                        '/jail/root/{0}/dev',                    None,   MS_BIND, None),
	('/dev/pts',                    '/jail/root/{0}/dev/pts',                None,   MS_BIND, None),
	('/jail/home/{0}/home',         '/jail/root/{0}/home',                   None,   MS_BIND, None),
	('/jail/home/{0}/etc/passwd',   '/jail/root/{0}/etc/passwd',             None,   MS_BIND, None),
	('/jail/home/{0}/etc/group',    '/jail/root/{0}/etc/group',              None,   MS_BIND, None),
	('/jail/home/{0}/var/log/wtmp', '/jail/root/{0}/var/log/wtmp',           None,   MS_BIND, None),
	('/jail/home/{0}/run/utmp',     '/jail/root/{0}/run/utmp',               None,   MS_BIND, None),
	('/jail/home/{0}/tmp',          '/jail/root/{0}/tmp',                    None,   MS_BIND, None),
	('/jail/home/{0}/home/{0}',     '/home/{0}',                             None,   MS_BIND, None),
	('/run/mysqld/mysqld.sock',     '/jail/root/{0}/run/mysqld/mysqld.sock', None,   MS_BIND, None),
)

# load list of mounted users
um_raw = map(lambda x: x.split(' ')[1].split('/'), open('/proc/mounts').readlines())
UserMounts = set([x[3] for x in um_raw if len(x) == 5 and x[2] == 'root' and x[4] == 'proc'])


# do a bind mount
def Mount(username, group='jail'):
	if username not in grp.getgrnam(group).gr_mem:
		raise 'User not in group %s' % group
	if pwd.getpwnam(username) and username not in UserMounts:
		print 'Mount(%s)' % username
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


# mount all jail users
def MountAll(group='jail'):
	for user in grp.getgrnam(group).gr_mem:
		Mount(user, group)


# detach umount a target
def Umount(username, group='jail'):
	if username not in grp.getgrnam(group).gr_mem:
		raise 'User not in group %s' % group
	if username in UserMounts:
		print 'Umount(%s)' % username
		for _, target, _, _, _ in MountPoints:
			libc.umount2(target.format(username), 2)
		UserMounts.remove(username)
		return True
	return False


# umount all jail users
def UmountAll(group='jail'):
	for user in grp.getgrnam(group).gr_mem:
		Umount(user, group)


# list all mounted users
def List(f=lambda x: True):
	return filter(f, UserMounts)
