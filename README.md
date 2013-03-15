About
-----

This is a set of tools that can be used to create, enable or disable chroot jails for web and shell hosting purposes.


Installation
------------

Install mandatory packages. At the very least we need git libpam-chroot to install software and confine ssh users to their jails.

	aptitude install gin libpam-chroot

Fetch jail code and make necessary links.

	cd /opt
	git clone https://github.com/phalaaxx/jail
	ln -s /opt/jail/jctl /usr/local/bin
	ln -s /opt/jail/jail /usr/lib/python2.7/dist-packages
	ln -s /opt/jail/etc/init.d/jail /etc/init.d

Enable jail init script. This script is used to bind-mount jail directories at boot time and umount them before shutdown.

	update-rc.d jail defaults
	update-rc.d jail enable

Make necessary directories.

	mkdir -p /jail/{base,root,home}

Create the jail users group.

	groupadd -g 990 -r jail

Download chroot environment.

	aptitude install debootstrap
	debootstrap --arch amd64 precise /jail/base http://archive.ubuntu.com/ubuntu/

Install necessary software within chroot environment, for example:

	chroot /jail/base apt-get install aptitude vim php5-cgi php5-mysql php5-gd


GRSecurity
----------

This is a simple introduction how to configure and install grsecurity patched kernel under ubuntu/debian. This step is optional though it is highly recommended.
Make sure you have sufficient space in /usr/src for kernel compilation before you proceed with the next step.
First, download necessary packages.

	aptitude install kernel-package libncurses5-dev gradm2 paxctl

Download grsecurity patch from http://grsecurity.net/download\_stable.php - at the time of writind latest stable version is 2.9.1-3.2.40-201303111844.

	cd /usr/src
	wget http://grsecurity.net/stable/grsecurity-2.9.1-3.2.40-201303111844.patch

Download and extract appropriate kernel version.

	wget https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.2.40.tar.xz
	tar Jxvf linux-3.2.40.tar.xz

Patch kernel sources with grsecurity patch.

	cd linux-3.2.40
	patch -p1 < ../grsecurity-2.9.1-3.2.40-201303111844.patch

Configure kernel sources.

	make menuconfig

Example setup has the following grsecurity options enabled (all options are under Security Options/Grsecurity/Customize Configuration). Options are for custom configuration method.

#### PaX ####
* Enable various PaX features
* PaX Control
  * Use ELF program header marking
* Non-executable pages
  * Enforce non-executable pages
  * Paging based non-executable pages
  * Emulate trampolines
  * Restrict mprotect()
* Address Space Layout Randomization
  * Address Space Layout Randomization
  * Randomize kernel stack base
  * Randomize user stack base
  * Randomize mmap() base
* Miscellaneous hardening features
  * Sanitize kernel stack
  * Prevent various kernel object reference counter overflows
  * Harden heap object copies between kernel and userland
  * Prevent various integer overflows in function size parameters
  * Generate some entropy during boot

#### Memory Protections ####
* Deny reading/writing to /dev/kmem, /dev/mem, and /dev/port
* Disable privileged I/O
* Harden BPF JIT against spray attacks
* Harden ASLR against information leaks and entropy reduction
* Deter exploit bruteforcing
* Harden module auto-loading
* Hide kernel symbols
* Active kernel exploit response

#### Role Based Access Control Options ####

#### Filesystem Protections ####
* Proc restrictions
  * Restrict /proc to user only
* Additional restrictions
* Linking restrictions
* FIFO restrictions
* Sysfs/debugfs restriction
* Runtime read-only mount protection
* Eliminate stat/notify-based device sidechannels
* Chroot jail restrictions
  * Deny mounts
  * Deny double-chroots
  * Deny pivot\_root in chroot
  * Enforce chdir("/") on all chroots
  * Deny (f)chmod +s
  * Deny fchdir out of chroot
  * Deny mknod
  * Deny shmat() out of chroot
  * Deny access to abstract AF\_UNIX sockets out of chroot
  * Protect outside processes
  * Restrict priority changes
  * Deny sysctl writes
  * Capability restrictions

#### Kernel Auditing ####
* /proc/<pid>/ipaddr support

#### Executable Protections ####
* Dmesg(8) restriction
* Deter ptrace-based process snooping
* Require read access to ptrace sensitive binaries
* Enforce consistent multithreaded privileges
* Trusted Path Execution (TPE)
  * Partially restrict all non-root users
  * GID for TPE-untrusted users (990)

#### Network Protections ####
* Larger entropy pools
* TCP/UDP blackhole and LAST\_ACK DoS prevention
* Disable TCP Simultaneous Connect
* Socket restrictions
  * Deny server sockets to group
  * GID to deny server sockets for (990)

Make sure to tune these settings to your liking. These settings may not work for your case.
Finally compile grsecurity kernel.

	make-kpkg --initrd --append-to-version "grsec" --revision 1 kernel_image

Depending on hardware this may take up to severas hours. Once the kernel is ready - install it.

	cd /usr/src
	dpkg -i linux-image-3.2.40-grsec_1_amd64.deb

At this point the server needs to be restarted. Once it boots make sure that the new kernel has been loaded.

	uname -r

If the server was booted into the new kernel. you should see something similar to _3.2.40-grsec_.
When the new kernel is running it is possible that some updates may fail due to grsecurity restrictions. The reason is because grub will not be able to update its configuration. In order to resolve this issue, two binaries from grub package need to be given correct permissions.

	paxctl -c /usr/bin/grub-script-check
	paxctl -c /usr/sbin/grub-probe
	paxctl -mpxe /usr/bin/grub-script-check
	paxctl -mpxe /usr/sbin/grub-probe


Apache
------

Install necessary apache and related packages.

	aptitude install apache2 libapache2-mod-suphp libapache2-mod-fcgid libapache2-mod-evasive mysql-server


Patch and compile suexec
------------------------

This step is optional. It is necessary if you are planning to run cgi and fcgi scripts in jail environment.
First fetch sources and build dependencies.

	mkdir /usr/src/suexec
	cd /usr/src/suexec
	apt-get source apache2-suexec
	apt-get build-dep apache2-suexec
	cd apache2-2.2.22

Patch the code. Edit _support/suexec.c_ file and add the following code before _setgid_ and _setuid_.

	    /*
	     * chroot to jail directory
	     */
	    char suexec_chroot[AP_MAXPATH];
	    char suexec_cwd[AP_MAXPATH];
	    if (getcwd(suexec_cwd, AP_MAXPATH) == NULL) {
	        log_err("cannot get current working directory: %s\n",
	                strerror(errno));
	        exit(301);
	    }
	    snprintf(suexec_chroot, AP_MAXPATH, "/jail/root/%s", pw->pw_name);
	    if (chroot(suexec_chroot)<0) {
	        log_err("cannot chroot to jail directory %s: %s\n",
	                suexec_chroot, strerror(errno));
	        exit(302);
	    }
	    if (chdir(suexec_cwd) != 0) {
	        log_err("cannot change directory to %s: %s\n",
	                suexec_cwd, strerror(errno));
	        exit(303);
	    }

Edit _debian/rules_ file and change default docroot to _/home_ and defailt userdir to www. Finally commit changes and build package.

	dpkg-source --commit
	dpkg-buildpackage

After a while the new packages set will be compiled. Install the appropriate package and make sure suexec binary is suid.

	cd /usr/src/suexec
	dpkg -i apache2-suexec_2.2.22-6ubuntu2.1_amd64.deb
	chmod +s /usr/lib/apache2/suexec

One last thing to do is to prevent package system from updating _apache2-suexec_ package.

	aptitude hold apache2-suexec

From now on cgi and fcgi binaries should be started within chroot jail in /jail/root/username directories. Of course, this will only work for mounted jails.


Usage
-----

In order to start using chroot jails you need some users in the jail group.

	adduser jtest
	usermod -aG jail jtest
	mkdir -p /var/log/apache2/hosting/juser
	
Update and mount jail directories.

	jctl --update
	jctl --mount jtest
	jctl --list


Sample vhost
------------

In order to make virtual hosts confined inside chroot jails, use configuration similar to this.

	<VirtualHost 91.230.230.227:80>
	        ServerAdmin webmaster@tauservice.eu
	        ServerName ut.deck17.com
	        DocumentRoot /home/jtest/www/jtest_vhost_root
	        SuexecUserGroup "jtest" "jtest"
	        LogLevel warn
	        ErrorLog ${APACHE_LOG_DIR}/hosting/jtest/jtest-error.log
	        CustomLog ${APACHE_LOG_DIR}/hosting/jtest/jtest-access.log combined
	</VirtualHost>


LICENSE
-------

BSD License http://opensource.org/licenses/bsd-license
