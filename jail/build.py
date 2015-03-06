from subprocess import call
from os.path import exists, dirname
from os import mkdir, chmod

# build suphp wrapper for jail chroot environment
def SuphpWrapper():
	wrapper = '/opt/jail/cgi-wrappers/suphp-wrapper'
	src = '/opt/jail/src/suphp-wrapper.c'

	if not exists(dirname(wrapper)):
		mkdir(dirname(wrapper))

	build = call([
		'gcc',
		'-o', wrapper,
		src])

	if not build and exists(wrapper):
		chmod(wrapper, 04755)
