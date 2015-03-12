#!/usr/bin/python

from subprocess import Popen, PIPE
from os.path import dirname, basename, join
from os.path import exists, islink, isfile, isdir
from os import makedirs, symlink, readlink
from os import mknod, makedev
from os import walk
from os import chmod
from stat import S_IFCHR, S_IFBLK
from shutil import copy, copystat


# list of files to copy
ChrootJailCopy = [
	# other libraries
	'/lib64/ld-linux-x86-64.so.2',
	'/lib/x86_64-linux-gnu/ld-2.19.so',

	# configuration
	'/etc/profile',
	'/etc/nsswitch.conf',

	# binaries
	'/bin/bash',
	'/bin/ls',
	'/bin/cat',
	'/bin/ping',
	'/usr/bin/id',
	'/usr/bin/whoami',

	# php stuff
	'/usr/bin/php5-cgi',
	'/usr/lib/php5']


# list of files to touch
ChrootJailTouch = [
	('etc/passwd',   0644, True),
	('etc/group',    0644, True),
	('var/log/wtmp', 0664, True),
	('run/utmp',     0664, True),
	('home',         0750, False),
	('tmp',          1777, False)]


# get all libraries used by binary
def GetLibDeps(LibDeps=[]):
	p = Popen(
		['/usr/bin/ldd', LibDeps[0]],
		stdout=PIPE)

	Libs = []
	for line in p.stdout.readlines():
		if '=>' in line:
			source, _, target, _ = line.strip().split()
			Libs.append(target)

	for lib in Libs:
		if lib in LibDeps:
			continue
		for l in GetLibDeps([lib] + Libs):
			if not l in Libs:
				Libs.append(l)
	return Libs


# copy a file and make symlinks
def CopyFileWithSymLinks(SrcFile, DestFile):
	# make sure destination directory exists
	if not isdir(dirname(DestFile)):
		makedirs(dirname(DestFile))

	if islink(SrcFile):
		# make a symlink
		print 'symlink(%s, %s)' % (DestFile, readlink(SrcFile))
		if not exists(DestFile):
			symlink(readlink(SrcFile), DestFile)
		RealSrcFile = join(dirname(SrcFile), readlink(SrcFile))
		RealDestFile = join(dirname(DestFile), readlink(SrcFile))
		CopyFileWithSymLinks(RealSrcFile, RealDestFile)

	if isfile(SrcFile):
		if exists(DestFile):
			print '... file %s already exists.' % DestFile
			return
		# make sure destination directory exists
		print 'copy(%s, %s)' % (SrcFile, DestFile)
		if not exists(DestFile):
			copy(SrcFile, DestFile)
			copystat(SrcFile, DestFile)
		return
	

# copy a file with all its dependencies to destination
def CopyFile(FileName, Dest='/jail/base'):
	for SrcFile in GetLibDeps([FileName]):
		Dir = dirname(SrcFile)
		DestDir = join(Dest, Dir[1:])
		DestFile = join(DestDir, basename(SrcFile))

		CopyFileWithSymLinks(SrcFile, DestFile)

	DestDir = join(Dest, dirname(FileName)[1:])
	CopyFileWithSymLinks(FileName, join(DestDir, basename(FileName)))


# copy directory tree
def CopyDirectory(DirectoryName, Dest='/jail/base'):
	for DirPath, DirNames, FileNames in walk(DirectoryName):
		for File in FileNames:
			DestFile = join(DirPath, File)
			CopyFile(DestFile, Dest)
		for Dir in DirNames:
			DestDir = join(DirPath, Dir)
			CopyDirectory(DestDir)


# create base files
def MakeBase(Dest='/jail/base'):
	BaseDirs = [
		'dev',
		'dev/pts',
		'proc',
		'bin',
		'usr',
		'usr/bin',
		'etc']

	for DestDir in map(lambda x: join(Dest, x), BaseDirs):
		if not exists(DestDir):
			makedirs(DestDir)

	DevFiles = [
		('dev/null',    0666, 1, 3),
		('dev/zero',    0666, 1, 5),
		('dev/console', 0600, 5, 1),
		('dev/tty',     0666, 5, 0)]

	for File, Mode, Major, Minor in DevFiles:
		DevFile = join(Dest, File)
		if not exists(DevFile):
			mknod(DevFile, Mode|S_IFCHR, makedev(Major, Minor))


# create/touch empty files
def TouchEmptyFiles(ChrootJailTouch, Dest='/jail/base'):
	for File, Mode, IsFile in ChrootJailTouch:
		Target = join(Dest, File)
		if not isdir(dirname(Target)):
			makedirs(dirname(Target))
		if not IsFile:
			if not isdir(Target):
				makedirs(Target)
				chmod(Target, Mode)
		if not exists(Target):
			open(Target, 'w+').close()
			chmod(Target, Mode)


# copy all files and directories from the list specified
def CopyJailFiles(ChrootJailCopy, Dest='/jail/base'):
	for Target in ChrootJailCopy:
		if isfile(Target):
			CopyFile(Target, Dest)
		if isdir(Target):
			CopyDirectory(Target)


# main program
if __name__ == '__main__':
	MakeBase()
	TouchEmptyFiles(ChrootJailTouch)
	CopyJailFiles(ChrootJailCopy)
