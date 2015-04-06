from os.path import join
from json import loads
from jinja2 import Template


VhostsTemplate = '''
# /etc/nginx/sites-enabled/{{UserName}}.conf
{% for vhost in vhosts %}server {
	listen 80;

	root /home/{{UserName}}/public_html;
	server_name {{vhost.Name}}{% if vhost.Aliases %}{% for alias in vhost.Aliases %} {{ alias }}{% endfor %}{% endif %};
	index index.php index.html index.htm;

	location ~ \.php$ {
		fastcgi_split_path_info ^(.+\.php)(/.+)$;
		fastcgi_pass unix:/var/run/php5-fpm/{{UserName}}.sock;
		fastcgi_index index.php;
		fastcgi_param PATH_TRANSLATED $document_root$fastcgi_script_name;
		include fastcgi_params;
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
