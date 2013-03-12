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
	JailDirectories = (
		('/home/{0}',				True),
		('/jail/root/{0}',			False),
		('/jail/home/{0}',			False),
		('/jail/home/{0}/etc',			False),
		('/jail/home/{0}/var',			False),
		('/jail/home/{0}/var/log',		False),
		('/jail/home/{0}/var/run',		False),
		('/jail/home/{0}/tmp',			False),
		('/jail/home/{0}/home',			False),
		('/jail/home/{0}/home/{0}',		True),
		('/jail/home/{0}/home/{0}/logs',	True),
		('/jail/home/{0}/home/{0}/www',		True),
		('/jail/home/{0}/home/{0}/mail',	True),
		('/var/log/apache2/hosting/{0}',	False),
	)

	# 3. create jail directories
	for dirname, chown in JailDirectories:
		dirname = dirname.format(user)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
			if chown:
				os.chown(
					dirname,
					pwd.getpwnam(user).pw_uid,
					pwd.getpwnam(user).pw_gid)

	# 4. create empty files
	for f in (os.path.join('/jail/home', user, 'var/log/wtmp'),
		os.path.join('/jail/home', user, 'var/log/utmp')):
		if not os.path.exists(f):
			open(f, 'w').close()

	# 5. generate custom passwd file
	passwd_path = os.path.join('/jail/home', user, 'etc/passwd')
	if not os.path.exists(passwd_path):
		userdata = [
			map(str, x) for x in
				[pw for pw in map(tuple, pwd.getpwall()) if
					pw[2] <= 100 or pw[0] == user]]
		open(passwd_path, 'w').write('\n'.join(map(':'.join, userdata))+'\n')

	# 6. generate custom group file
	group_path = os.path.join('/jail/home', user, 'etc/group')
	if not os.path.exists(group_path):
		groupdata = [
			map(str, gr[0:3]) + [','.join(gr[3])] for gr in
				map(tuple, grp.getgrall()) if
					gr[2] <= 100 or gr[0] == user or user in gr[3]]
		open(group_path, 'w').write('\n'.join(map(':'.join, groupdata))+'\n')


# update all jail user directories
def UpdateGroup(group='jail'):
	for user in grp.getgrnam(group).gr_mem:
		UpdateUser(user)
	UpdateChroot(group)
