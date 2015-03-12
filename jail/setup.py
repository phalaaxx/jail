from platform import machine
from subprocess import call
from grp import getgrall
from os import symlink
from os.path import exists, isdir, islink, dirname

# packages to install in chroot environment
DefaultPackages = [
	'php5-cgi',
	'php5-mysql',
	'php5-gd']

# setup a chroot environment
def ChrootSetup():
	ArchType = {
		'i386'		: 'i386',
		'x86_64'	: 'amd64'}
	return call([
		'/usr/sbin/debootstrap',
		'--arch', ArchType.get(machine(), 'amd64'),
		'--include', ' '.join(DefaultPackages),
		'jessie',
		'/jail/base',
		'http://ftp.debian.org/debian/'])

# update chroot environment
def ChrootUpdate():
	return call([
		'/usr/sbin/chroot',
		'/jail/base',
		'apt-get', 'update'])
	
# upgrade chroot environment
def ChrootUpgrade():
	return call([
		'/usr/sbin/chroot',
		'/jail/base',
		'apt-get', '-y', 'upgrade'])

# setup jail groups
def GroupsSetup():
	DefaultGroups = (
		('jail',		990),
		('jailtpe',		991),
		('jailsocket',	992),
		('jailcsocket',	993),
		('jailssocket',	994))

	SysGroups = getgrall()

	for DefaultGroup, DefaultGroupID in DefaultGroups:
		if DefaultGroup in map(lambda x: x.gr_name, SysGroups):
			print 'Group with name %s already exists.' % DefaultGroup
			continue
		if DefaultGroupID in map(lambda x: x.gr_gid, SysGroups):
			print 'Group with ID %d already exists.' % DefaultGroupID
			continue
		# add DefaultGroup with DefaultGroupID
		groupadd = call([
			'groupadd',
			'-g', str(DefaultGroupID),
			DefaultGroup])
		if not groupadd:
			print 'Created group %s with id %d' % (DefaultGroup, DefaultGroupID)


# make initial symlinks setup
def SymLinksSetup():
	DefaultLinks = (
		('/opt/jail/jctl',                                 '/usr/local/bin/jctl'),
		('/opt/jail/jail',                                 '/usr/lib/python2.7/dist-packages/jail'),
		('/opt/jail/etc/init.d/jail',                      '/etc/init.d/jail'),
		('/opt/jail/etc/apache2/conf-available/jail.conf', '/etc/apache2/conf-available/jail.conf'))

	for src, dst in DefaultLinks:
		if isdir(dirname(dst)):
			if exists(dst):
				print 'File exists: %s' % dst
				continue
			symlink(src, dst)
			print '%s -> %s' % (src, dst)