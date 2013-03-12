import re
import os
import shutil
import pwd
import grp

from jail import mount


# vhosts
coServerName    = re.compile('^\tServerName (.+)$')
coServerAlias   = re.compile('^\tServerAlias (.+)$')
coVHostBegin    = re.compile('^<VirtualHost ([\d,\.]+):(\d+)>$')
coVHostEnd      = re.compile('^</VirtualHost>')

# filenames
fnApacheConf = lambda username: '/etc/apache2/sites-enabled/{0}.conf'.format(username)
fnDocRoot = lambda x: '/home/{UserName}/www/{ServerName}'.format(**x)
fnAccessLog = lambda u, s: '/var/log/apache2/hosting/{0}/{1}-access.log'.format(u, s)
fnErrorLog = lambda u, s: '/var/log/apache2/hosting/{0}/{1}-error.log'.format(u, s)



# read virtual host from a file
def Read(username):
	if os.path.exists(fnApacheConf(username)):
		fp = open(fnApacheConf(username), 'r')
		read = False
		vhosts = []
		vh = {}
		while True:
			line = fp.readline()
			if not line:
				return vhosts

			if not read:
				mo = coVHostBegin.match(line)
				if mo is not None:
					vh = {
						'UserName'      : username,
						'ServerAddress' : mo.group(1),
						'ServerName'    : None,
						'IsHttps'       : mo.group(2) == '443',
						'ServerAlias'   : [],
					}
					read = True
			else:  
				mo = coServerName.match(line)
				if mo: 
					vh['ServerName'] = mo.group(1)
					continue
				mo = coServerAlias.match(line)
				if mo: 
					vh['ServerAlias'].append(mo.group(1))
					continue
				mo = coVHostEnd.match(line)
				if mo: 
					vhosts.append(vh)
					read = False
	return []


# write vhost to a file
def Write(vhosts):
	# take username from first vhost
	if len(vhosts):
		username = vhosts[0]['UserName']
		fp = open(fnApacheConf(username), 'w')
		for vh in vhosts:
			
			data = {
				'UserName'	: vh['UserName'],
				'ServerAddress'	: vh['ServerAddress'],
				'Port'		: 80,
				'ServerName'	: vh['ServerName'],
				'ServerAlias'	: vh['ServerAlias'],
			}
			if vh['IsHttps']:
				data['Port'] = 443
			vhost = '<VirtualHost {ServerAddress}:{Port}>\n'
			vhost += '\tServerAdmin postmaster@tauhosting.com\n'
			vhost += '\tServerName {ServerName}\n'
			for alias in vh['ServerAlias']:
				vhost += '\tServerAlias {Alias}\n'.format(Alias=alias)
			vhost += '\tDocumentRoot /home/{UserName}/www/{ServerName}\n'
			vhost += '\tCustomLog ${{APACHE_LOG_DIR}}/hosting/{UserName}/{ServerName}-access.log combined\n'
			vhost += '\tErrorLog ${{APACHE_LOG_DIR}}/hosting/{UserName}/{ServerName}-error.log\n'
			vhost += '</VirtualHost>\n\n'
			fp.write(vhost.format(**data))
		fp.close()
		return True, len(vhosts)
	return False, False


# add or edit virtual host
def Update(vhost):
	# 1. make sure user exists
	pw = pwd.getpwnam(vhost['UserName'])
	if not pw:
		return False, 'User {UserName} does not exist!'.format(**vhost)
	# 2. copy old configuration
	vhosts_in = Read(vhost['UserName'])
	vhosts_out = []
	for vh in vhosts_in:
		if vh['ServerName'] != vhost['ServerName']:
			vhosts_out.append(vh)
	# 3. copy new/updated virtual host
	vhosts_out.append(vhost)
	Write(vhosts_out)
	# 4. make sure docroot exists
	if not os.path.exists(fnDocRoot(vhost)):
		os.mkdir(fnDocRoot(vhost))
		os.chown(fnDocRoot(vhost), int(pw.pw_uid), 999)
	# 5. activate new configuration
	r = Apache2CtlGraceful()
	if r:
		return False, 'Apache graceful error!'
	return True, True


# remove virtual host
def Remove(username, servername=None):
	# 1. make sure user exists
	pw = pwd.getpwnam(username)
	if not pw:
		return False, 'User {0} does not exist!'.format(username)
	# 2. remove vhost/configuration
	if not servername:
		# 2.1 remove configuration file
		if os.path.exists(fnApacheConf(username)):
			os.unlink(fnApacheConf(username))
	else:
		# 2.2 remove vhost
		vhosts_in = Read(username)
		vhosts_out = []
		for vh in vhosts_in:
			if vh['ServerName'] != servername:
				vhosts_out.append(vh)
		Write(vhosts_out)
	# 3. activate new configuration
	r = Apache2CtlGraceful()
	if r:
		return False, r
	return True, True


# get latest access log lines
def AccessLog(username, servername, lines=200):
	if os.path.exists(fnAccessLog(username, servername)):
		return True, ''.join(open(fnAccessLog(username, servername), 'r').readlines()[-lines:])


# get latest error log lines
def ErrorLog(username, servername, lines=200):
	if os.path.exists(fnErrorLog(username, servername)):
		return True, ''.join(open(fnErrorLog(username, servername), 'r').readlines()[-lines:])
	return False, fnErrorLog(username, servername)
