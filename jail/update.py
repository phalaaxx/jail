import os
import pwd
import grp
from os.path import exists, isdir
from os.path import join, dirname
from os import makedirs, walk
from os import link

from jail.user import UpdateUserJail

# constants
JailBase = '/jail/base'

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
		('/home/{0}',                           True,  00750),
		('/jail/backup/{0}',                    False, 00750),
		('/jail/root/{0}',                      False, 00755),
		('/jail/home/{0}',                      False, 00750),
		('/jail/home/{0}/etc',                  False, 00755),
		('/jail/home/{0}/var',                  False, 00755),
		('/jail/home/{0}/var/log',              False, 00755),
		('/jail/home/{0}/run',                  False, 00755),
		('/jail/home/{0}/tmp',                  False, 01777),
		('/jail/home/{0}/home',                 False, 00755),
		('/jail/home/{0}/home/{0}',             True,  00750),
		('/jail/home/{0}/home/{0}/logs',        True,  00755),
		('/jail/home/{0}/home/{0}/public_html', True,  00750),
		('/jail/home/{0}/home/{0}/mail',        True,  00750),
	)

	# 2. create jail root
	JailRoot = '/jail/root/{0}'.format(user)
	if not exists(JailRoot):
		makedirs(JailRoot)

	for SrcPath, DirNames, FileNames in walk(JailBase):
		RelPath = SrcPath[len(JailBase)+1:]

		# make directories
		for Dir in DirNames:
			DstDir = join(JailRoot, RelPath, Dir)
			if not isdir(DstDir):
				makedirs(DstDir)

		# copy hardlinks
		for File in FileNames:
			DstPath = join(JailRoot, RelPath)

			# make sure destination directory exists
			if not isdir(DstPath):
				makedirs(DstPath)

			SrcFile = join(SrcPath, File)
			DstFile = join(DstPath, File)

			# make a hard link
			if not exists(DstFile):
				link(SrcFile, DstFile)

	# 3. create jail directories
	for DirName, chown, mode in JailDirectories:
		DirName = DirName.format(user)
		if not os.path.exists(DirName):
			os.makedirs(DirName)
			if chown:
				os.chown(
					DirName,
					pwd.getpwnam(user).pw_uid,
					pwd.getpwnam(user).pw_gid)
		os.chmod(DirName, mode)

	# 4. create empty files
	for f in (os.path.join('/jail/home', user, 'var/log/wtmp'),
		os.path.join('/jail/home', user, 'run/utmp')):
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

	# 7. update user jail
	UpdateUserJail(user)


# update all jail user directories
def UpdateGroup(group='jail'):
	for user in grp.getgrnam(group).gr_mem:
		UpdateUser(user)
	UpdateChroot(group)
