import pwd
import spwd
import grp
from os.path import exists, isdir, islink, join, dirname
from os import walk, makedirs, readlink, link, symlink, rename, chown, chmod, fdopen, unlink
from tempfile import mkstemp
from time import time


# constants
JailBase = '/jail/base'
MinID = 1000
MaxID = 10000

# a set of all allowed user IDs
AllowedUserIDs = set(range(MinID, MaxID))
AllowedGroupIDs = set(range(MinID, MaxID))


## chroot related methods

# update pam_chroot configuration
def UpdateSecurityChroot(group='jail'):
	# update chroot pam configuration
	open('/etc/security/chroot.conf', 'w+').write(
		'\n'.join(
			map(lambda x: '{0} /jail/root/{0}'.format(x), grp.getgrnam(group).gr_mem))+'\n')


# get list of all used user ids
def GetUserIDs():
	UserIDs = map(
		lambda x: x.pw_uid,
		pwd.getpwall())
	return set(filter(
		lambda x: x >= MinID and x <= MaxID,
		UserIDs))


# get list of all used group ids
def GetGroupIDs():
	GroupIDs = map(
		lambda x: x.gr_gid,
		grp.getgrall())
	return set(filter(
		lambda x: x >= MinID and x <= MaxID,
		GroupIDs))


# return shadow file item
def ShadowItem(x):
	if type(x) == int and x == -1:
		return ''
	return str(x)


# return group file item
def GroupItem(x):
	if type(x) == list:
		return ','.join(x)
	return str(x)


# create entry in passwd file for new user
def UserAdd_Passwd(User, PasswdFile='/etc/passwd'):
	# 1. temporary file
	fd, TempPasswdFile = mkstemp(prefix='passwd', dir='/tmp')

	# 2. get minimum available user and group IDs
	UserID = min(
		AllowedUserIDs.difference(GetUserIDs()))

	GroupIDs = AllowedGroupIDs.difference(GetGroupIDs())
	GroupID = min(GroupIDs)
	if GroupID != UserID and UserID in GroupIDs:
		GroupID = UserID
	
	# 3. prepare passwd
	pw_user = pwd.struct_passwd(
		sequence = (
			User,
			'x',
			UserID,
			GroupID,
			'',
			join('/home', User),
			'/bin/bash'))

	# 4. generate temporary passwd file
	pwall = pwd.getpwall()
	pwall.append(pw_user)
	pwall.sort(lambda a, b: cmp(a.pw_uid, b.pw_uid))
	with fdopen(fd, 'w+') as fh:
		for pw in pwall:
			fh.write(':'.join(map(lambda x: str(x), pw))+'\n')

	# 5. activate new passwd file
	rename(TempPasswdFile, PasswdFile)
	chown(PasswdFile, 0, 0)
	chmod(PasswdFile, 0644)


# create entry in shadow file for new user
def UserAdd_Shadow(User, Passwodr='*', ExpireDays=-1, ShadowFile='/etc/shadow'):
	# 1. temporary shadow file
	fd, TempShadowFile = mkstemp(prefix='shadow', dir='/tmp')

	# 2. get users passwd entries
	pwall = pwd.getpwall()
	pwall.sort(lambda a, b: cmp(a.pw_uid, b.pw_uid))

	# 3. generate shadow entries
	CreatedDays = int(time() / 86400)
	if ExpireDays != -1:
		ExpireDays = CreatedDays + ExpireDays

	spall = []
	for pw in pwall:
		try:
			sp = spwd.getspnam(pw.pw_name)
		except KeyError, e:
			sp = spwd.struct_spwd(
				sequence = (
					User,
					'*',
					CreatedDays,
					0,
					99999,
					7,
					-1,
					ExpireDays,
					-1))
		spall.append(sp)

	# 4. generate temporary shadow file
	with fdopen(fd, 'w+') as fh:
		for sp in spall:
			fh.write(':'.join(map(ShadowItem, sp))+'\n')

	# 5. activate new shadow file
	rename(TempShadowFile, ShadowFile)
	chown(ShadowFile, 0, 0)
	chmod(ShadowFile, 0600)


# create entry in group file for new user
def UserAdd_Group(User, GroupFile='/etc/group'):

	# 1. temporary file
	fd, TempGroupFile  = mkstemp(prefix='group',  dir='/tmp')

	# 2. add new group entry
	pw = pwd.getpwnam(User)
	gr = grp.struct_group(
		sequence = (
			User,
			'x',
			pw.pw_gid,
			['www-data']))

	grall = grp.getgrall()
	grall.append(gr)
	grall.sort(lambda a, b: cmp(a.gr_gid, b.gr_gid))

	# 3. write groups to temporary file
	with fdopen(fd, 'w+') as fh:
		for gr in grall:
			if gr.gr_name in ['www-data', 'jail'] and User not in gr.gr_mem:
				gr.gr_mem.append(User)
			fh.write(':'.join(map(GroupItem, gr))+'\n')

	# 4. activate new group file
	rename(TempGroupFile, GroupFile)
	chown(GroupFile, 0, 0)
	chmod(GroupFile, 0644)
	

# create jail root directories
def UpdateUserJail(User, DestDir='/jail/root'):
	# 0. helper methods
	users = []
	def filterUsers(user):
		for pw in pwd.getpwall():
			if pw.pw_uid <= 100 or pw.pw_name == user:
				users.append(pw.pw_name)
				yield ':'.join(map(str, pw))

	def filterGroups(user):
		for gr in grp.getgrall():
			if gr.gr_gid <= 100 or gr.gr_name == user or user in gr.gr_mem:
				gr = gr[0:3] + tuple([','.join(filter(lambda x: x in users, gr.gr_mem))])
				yield ':'.join(map(str, gr))

	# 1. create jail root
	JailRoot = '/jail/root/{0}'.format(User)
	if not exists(JailRoot):
		makedirs(JailRoot)

	# 2. hard link binaries and libraries
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

			# make soft links
			if islink(SrcFile):
				if not islink(DstFile):
					symlink(readlink(SrcFile), DstFile)
			elif not exists(DstFile):
				# make a hard link
				link(SrcFile, DstFile)

	# 3. prepare custom group and passwd files
	PasswdPath = join(DestDir, User, 'etc/passwd')
	with open(PasswdPath, 'w+') as fh:
		fh.write('\n'.join(filterUsers(User))+'\n')
	chmod(PasswdPath, 0644)

	GroupPath = join(DestDir, User, 'etc/group')
	with open(GroupPath, 'w+') as fh:
		fh.write('\n'.join(filterGroups(User))+'\n')
	chmod(GroupPath, 0644)

	# 4. create empty files in chroot jail
	ChrootJailTouch = [
		('var/log/wtmp',     0664, True),
		('run/utmp',         0664, True),
		('home',             0750, False),
		(join('home', User), 0750, False),
		('tmp',              1777, False)]

	for File, Mode, IsFile in ChrootJailTouch:
		Target = join(DestDir, User, File)
		if not isdir(dirname(Target)):
			makedirs(dirname(Target))
		if not IsFile:
			if not isdir(Target):
				makedirs(Target)
				chmod(Target, Mode)
		if not exists(Target):
			open(Target, 'w+').close()
			chmod(Target, Mode)

	# 5. create home directories and copy default templates
	pw = pwd.getpwnam(User)
	JailHomeDir = join('/jail/home', User)
	HomeDirs = (
		JailHomeDir,
		join(JailHomeDir, 'public_html'),
		join(JailHomeDir, 'mail'),
		join(JailHomeDir, '.ssh'))

	for HomeDir in HomeDirs:
		if not isdir(HomeDir):
			makedirs(HomeDir)
			chown(HomeDir, pw.pw_uid, pw.pw_gid)
			chmod(HomeDir, 0750)
	
	# 6. template files in home directory
	

# create a new system user
def UserAdd(User, Password='*', ExpireDays=-1):
	# 1. sanity checks
	try:
		pwd.getpwnam(User)
		print 'Already exists'
		return
	except KeyError, e:
		pass

	# 2. create system user and group
	UserAdd_Passwd(User)
	UserAdd_Shadow(User)
	UserAdd_Group(User)

	# 3. create/update user jail
	UpdateUserJail(User)

	# 4. other initializations
	UpdateSecurityChroot()

	# make home directory
	HomeDir = join('/home', User)
	if not isdir(HomeDir):
		makedirs(HomeDir)


# remove user from passwd file
def UserDel_Passwd(User, PasswdFile='/etc/passwd'):
	# 1. temporary file
	fd, TempPasswdFile = mkstemp(prefix='passwd', dir='/tmp')

	# 2. generate temporary passwd file
	with fdopen(fd, 'w+') as fh:
		for pw in pwd.getpwall():
			if pw.pw_name != User:
				fh.write(':'.join(map(lambda x: str(x), pw))+'\n')
	
	# 3. activate new passwd file
	rename(TempPasswdFile, PasswdFile)
	chown(PasswdFile, 0, 0)
	chmod(PasswdFile, 0644)


# remove user from shadow file
def UserDel_Shadow(User, ShadowFile='/etc/shadow'):
	# 1. temporary shadow file
	fd, TempShadowFile = mkstemp(prefix='shadow', dir='/tmp')

	# 2. generate temporary shadow file
	with fdopen(fd, 'w+') as fh:
		for sp in spwd.getspall():
			if sp.sp_nam != User:
				fh.write(':'.join(map(ShadowItem, sp))+'\n')

	# 3. activate new shadow file
	rename(TempShadowFile, ShadowFile)
	chown(ShadowFile, 0, 0)
	chmod(ShadowFile, 0600)


# remove group from group file
def UserDel_Group(User, GroupFile='/etc/group'):
	# 1. temporary file
	fd, TempGroupFile = mkstemp(prefix='group', dir='/tmp')

	# 2. generate temporary group file
	with fdopen(fd, 'w+') as fh:
		for gr in grp.getgrall():
			if gr.gr_name != User:
				if User in gr.gr_mem:
					gr.gr_mem.remove(User)
				fh.write(':'.join(map(GroupItem, gr))+'\n')
	
	# 3. activate new group file
	rename(TempGroupFile, GroupFile)
	chown(GroupFile, 0, 0)
	chmod(GroupFile, 0644)
	

# remove user
def UserDel(User):
	# remove user and group
	UserDel_Passwd(User)
	UserDel_Shadow(User)
	UserDel_Group(User)

	# other initializations
	UpdateSecurityChroot()
