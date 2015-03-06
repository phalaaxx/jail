from subprocess import call

# graceful restart
def Graceful():
	return call([
		'/usr/sbin/apache2ctl',
		'graceful'])


# test apache configuration
def ConfigTest():
	return call([
		'/usr/sbin/apache2ctl',
		'configtest'])
