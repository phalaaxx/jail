import os

# graceful restart
def Graceful():
	return os.system('/usr/sbin/apache2ctl graceful > /dev/null 2>&1')


# test apache configuration
def ConfigTest():
	return os.system('/usr/sbin/apache2ctl configtest > /dev/null 2>&1')
