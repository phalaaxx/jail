import os
import pwd


# create new mysql user
def MySQLCreateUser(username, password):
	pass


def MySQLDropUser(username):
	# remove all user databases
	pass


# create user database
def MySQLCreateDB(username, database):
	pw = pwd.getpwnam(username)
	if not pw:
		return False, 'User {0} does not exist!'.format(username)

	if os.path.exist(fnDatabase(database)):
		return False, 'Database {0} already exists!'.format(database)

	mysql_gid = int(pwd.getpwnam('mysql').pw_gid)

	# 1. create new database
	os.mkdir(fnDatabase(database))
	os.chown(fnDatabase(database), int(pw.pw_uid), mysql_gid)
	open(fnDatabaseOpt(database), 'w').write('default-character-set=utf8\ndefault-collation=utf8_general_ci\n')
	chown(fnDatabaseOpt(database), int(pw.pw_uid), mysql_gid)

	# 2. create user with rights to database
	cr.execute('GRANT ALL PRIVILEGES ON {0}.* TO "{1}"@"localhost";'.format(database, username))

	return True, True


# drop user database
def MySQLDropDB(database, cr):
	# get user data
	if not os.path.exists(fnDatabase(database)):
		return False, 'Database {0} does not exist!'.format(database)
	pw = pwd.getpwnam(os.stat(fnDatabase(database)).st_uid)
	
	# get owner of database
	cr.execute('REVOKE ALL PRIVILEGES ON {0}.* FROM ')
