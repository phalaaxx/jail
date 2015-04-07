from os.path import join
from os.path import exists
from os import unlink
from json import loads
from jinja2 import Template


VhostsTemplate = '''
# /etc/nginx/sites-enabled/{{UserName}}.conf
{% for vhost in vhosts %}server {
	listen 80;

	root /home/{{UserName}}/public_html;
	server_name {{vhost.Name}}{% if vhost.Aliases %}{% for alias in vhost.Aliases %} {{ alias }}{% endfor %}{% endif %};
	index index.php index.html;

	location ~ \.php$ {
		include uwsgi_params;
		uwsgi_modifier1 14;
		uwsgi_pass unix:///jail/root/{{UserName}}/run/uwsgi/app/php-uwsgi.sock;
	}

}
{% endfor %}
'''

# name of configuration file
fnConfigFile = lambda user: join('/etc/nginx/sites-enabled', '%s.conf' % user)


# generate user's vhosts file from json encoded data
def UpdateNginxConf(VhostData):
	template = Template(VhostsTemplate)
	with open(fnConfigFile(VhostData.get('UserName')), 'w+') as fh:
		fh.write(template.render(**VhostData))


# remove user's nginx configuration
def RemoveNginxConf(user):
	if exists(fnConfigFile(user)):
		unlink(fnConfigFile(user))
