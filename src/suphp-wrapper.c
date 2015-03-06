#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pwd.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>
#include <linux/limits.h>

/* main program */
int main(void) {
	/*
	 * TODO: prepare safe environment for php5-cgi
	 */

	/*
	 * get file stat
	 */
	char *path_translated;
	struct stat st;
	path_translated = getenv("PATH_TRANSLATED");
	if (stat(path_translated, &st) != 0) {
		fprintf(stderr, "cannot get file stats for %s: %s\n",
		        path_translated, strerror(errno));
		exit(101);
	}

	/*
	 * get user information
	 */
	struct passwd *pw;
	if ((pw = getpwuid(st.st_uid)) == NULL) {
		fprintf(stderr, "cannot get user information about uid %d: %s\n", 
		        st.st_uid, strerror(errno));
		exit(102);
	}

	/*
	 * security checks
	 */
	if (strstr(path_translated, "/../") != NULL) {
		fprintf(stderr, "invalid command %s",
		        path_translated);
		exit(103);
	}

	/*
	 * get script working directory
	 */
	char suphp_cwd[PATH_MAX];
	char *last;
	int path_len;
	struct stat cwd_st;
	last = rindex(path_translated, '/');
	path_len = last - path_translated;
	if (path_len > PATH_MAX) {
		fprintf(stderr, "script directory name is too long: %s\n",
		        path_translated);
		exit(104);
	}
	if (last == NULL) {
		fprintf(stderr, "cannot find script working directory for %s\n",
		        path_translated);
		exit(105);
	}
	strncpy(suphp_cwd,
	        path_translated,
	        last - path_translated);

	/*
	 * more security checks
	 */
	if (stat(suphp_cwd, &cwd_st) != 0) {
		fprintf(stderr, "cannot stat script working directory for %s: %s\n",
		        suphp_cwd, strerror(errno));
		exit(106);
	}
	if (cwd_st.st_uid != pw->pw_uid) {
		fprintf(stderr, "script directory has incorrect user ownership: %d\n",
		        cwd_st.st_uid);
		exit(107);
	}
	if (cwd_st.st_gid != pw->pw_gid) {
		fprintf(stderr, "script directory has incorrect group ownership: %d\n",
		        cwd_st.st_gid);
		exit(108);
	}

	/*
	 * chroot to jail directory
	 */
	char suphp_chroot[PATH_MAX];
	snprintf(suphp_chroot, PATH_MAX, "/jail/root/%s", pw->pw_name);
	if (chroot(suphp_chroot) < 0) {
		fprintf(stderr, "cannot chroot to jail directory %s: %s\n",
		        suphp_chroot, strerror(errno));
		exit(109);
	}
	if (chdir(suphp_cwd) != 0) {
		fprintf(stderr, "cannot change directory to %s: %s\n",
		        suphp_cwd, strerror(errno));
		exit(110);
	}

	/*
	 * drop privileges
	 */
	if (setgid(st.st_gid) != 0) {
		fprintf(stderr, "cannot set group id %d: %s\n",
		        st.st_gid, strerror(errno));
		exit(111);
	}
	if (setuid(st.st_uid) != 0) {
		fprintf(stderr, "cannot set user id %d: %s\n",
		        st.st_uid, strerror(errno));
		exit(112);
	}

	/*
	 * exec php binary
	 */
	execl(
		"/usr/bin/php5-cgi",
		path_translated,
		(char *)NULL);

	/*
	 * exec failed, print error
	 */
	fprintf(stderr, "cannot exec php5-cgi %s: %s\n",
	        path_translated, strerror(errno));
	exit(114);
}
