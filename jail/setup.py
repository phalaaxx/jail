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
