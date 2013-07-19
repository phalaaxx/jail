import os
import pwd
import grp


# update pam_chroot configuration
def UpdateChroot(group='jail'):
	# update chroot pam configuration
	open('/etc/security/chroot.conf', 'w+').write(
		'\n'.join(
			map(lambda x: '{0} /jail/root/{0}'.format(x), grp.getgrnam(group).gr_mem))+'\n')

	
# update jail user directories
def UpdateUser(user):
	users = []
	def filterUsers(user):
		for pw in map(tuple, pwd.getpwall()):
			if pw[2] <= 100 or pw[0] == user:
				users.append(pw[0])
				yield ':'.join(map(str, pw))

	def filterGroups(user):
		for gr in map(tuple, grp.getgrall()):
			if gr[2] <= 100 or gr[0] == user or user in gr[3]:
				gr = gr[0:3] + tuple([','.join(filter(lambda x: x in users, gr[3]))])
				yield ':'.join(map(str, gr))

	JailDirectories = (
		('/home/{0}',				True,		00750),
		('/jail/backup/{0}',			False,		00750),
		('/jail/root/{0}',			False,		00755),
		('/jail/home/{0}',			False,		00750),
		('/jail/home/{0}/etc',			False,		00755),
		('/jail/home/{0}/var',			False,		00755),
		('/jail/home/{0}/var/log',		False,		00755),
		('/jail/home/{0}/var/run',		False,		00755),
		('/jail/home/{0}/tmp',			False,		01777),
		('/jail/home/{0}/home',			False,		00755),
		('/jail/home/{0}/home/{0}',		True,		00750),
		('/jail/home/{0}/home/{0}/logs',	True,		00755),
		('/jail/home/{0}/home/{0}/www',		True,		00750),
		('/jail/home/{0}/home/{0}/mail',	True,		00750),
		('/var/log/apache2/hosting/{0}',	False,		00755),
	)

	# 3. create jail directories
	for dirname, chown, mode in JailDirectories:
		dirname = dirname.format(user)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
			if chown:
				os.chown(
					dirname,
					pwd.getpwnam(user).pw_uid,
					pwd.getpwnam(user).pw_gid)
		os.chmod(dirname, mode)

	# 4. create empty files
	for f in (os.path.join('/jail/home', user, 'var/log/wtmp'),
		os.path.join('/jail/home', user, 'var/run/utmp')):
		if not os.path.exists(f):
			open(f, 'w').close()
		os.chmod(f, 0644)

	# 5. generate custom passwd file
	passwd_path = os.path.join('/jail/home', user, 'etc/passwd')
	open(passwd_path, 'w+').write('\n'.join(filterUsers(user))+'\n')
	os.chmod(passwd_path, 0644)

	# 6. generate custom group file
	group_path = os.path.join('/jail/home', user, 'etc/group')
	open(group_path, 'w+').write('\n'.join(filterGroups(user))+'\n')
	os.chmod(group_path, 0644)


# update all jail user directories
def UpdateGroup(group='jail'):
	for user in grp.getgrnam(group).gr_mem:
		UpdateUser(user)
	UpdateChroot(group)
