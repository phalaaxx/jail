from platform import machine
from subprocess import call

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
