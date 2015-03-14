from distutils.core import setup, Extension

setup(
    name             = 'jail',
    version          = '0.1',
    description      = 'Python chroot jail environments module for web and shell hosting purposes',
    long_description = 'This is a Python 2.7.x package and commandline tool to easily create and update chroot jail environments',
    author           = 'Bozhin Zafirov',
    author_email     = 'bozhin@abv.bg',
    packages         = ['jail'],
    license          = 'BSD',
    data_files       = [
        ('/usr/sbin',                   ['sbin/jctl']),
        ('/etc/init.d',                 ['etc/init.d/jail']),
        ('/etc/apache2/conf-available', ['etc/apache2/conf-available/jail.conf'])],
)
