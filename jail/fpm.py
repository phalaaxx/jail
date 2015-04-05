from subprocess import call
from os.path import exists
from os.path import join
from os import makedirs
from os import unlink
from grp import getgrnam


fpmTemplate = '''# /etc/php5/fpm/pool.d/{user}
[{user}]

user = {user}
group = {user}

listen = /var/run/php5-fpm/{user}.sock

listen.owner = {user}
listen.group = {user}

pm = dynamic
pm.max_children = {max_children}
pm.start_servers = {servers}
pm.min_spare_servers = {min_spares}
pm.max_spare_servers = {max_spares}

chroot = /jail/root/{user}
chdir = /home/{user}/public_html
'''


# get the name of user fpm file
fpmFile = lambda user: join('/etc/php5/fpm/pool.d', '%s.conf' % user)


# attempt reload, fallback to full restart
def fpmReload():
	with open('/dev/null', 'w+') as NULL:
		ret = call([
			'/etc/init.d/php5-fpm',
			'reload'],
			stdout = NULL,
			stderr = NULL)
		if ret == 0:
			return ret
		return call([
			'/etc/init.d/php5-fpm',
			'restart'],
			stdout = NULL,
			stderr = NULL)
		

# create php5-fpm configuration file for user specified
def fpmConfigureUser(User, MaxChildren=15, Servers=2, MinSpares=1, MaxSpares=3):
	if not exists(fpmFile(User)):
		with open(fpmFile(User), 'w+') as fh:
			fh.write(
				fpmTemplate.format(
					user         = User,
					max_children = MaxChildren,
					servers      = Servers,
					min_spares   = MinSpares,
					max_spares   = MaxSpares))


# remove fpm user file
def fpmDeconfigureUser(User):
	if exists(fpmFile(User)):
		unlink(fpmFile(User))


# configure all user fpm pools
def ConfigureAll(UserMounts, group='jail'):
	for user in getgrnam(group).gr_mem:
		if user in UserMounts:
			fpmConfigureUser(user)
		else:
			fpmDeconfigureUser(user)
	fpmReload()
