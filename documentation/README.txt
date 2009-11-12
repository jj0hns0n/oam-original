OpenAerialMap
=============

Using TileCache: point TileCache config to the settings.MAPFILE_LOCATION, like
so:

[openaerialmap]
type=MapServerLayer
mapfile=/var/www/oam/mapfile/oam.map
layers=world
extension=jpeg
levels=25

[openaerialmap-900913]
type=MapServerLayer
mapfile=/var/www/oam/mapfile/oam.map
layers=world
extension=jpeg
levels=25
srs=EPSG:900913
bbox=-20037508,-20037508,20037508,20037508
maxresolution=156543.0339
metasize=2,2
metatile=yes


Apache config:

NameVirtualHost *
<VirtualHost *>
    ServerAdmin crschmidt@crschmidt.net
    ServerName openaerialmap.hypercube.telascience.org
    ServerAlias crschmidt.hypercube.telascience.org

    DocumentRoot /var/www/oam/docs
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/oam/docs>
        Options Indexes FollowSymLinks MultiViews ExecCGI
        AllowOverride None
        Order allow,deny
        allow from all
    </Directory>

    ErrorLog /var/log/apache2/error.log
    LogLevel warn

    CustomLog /var/log/apache2/access.log combined
    ServerSignature Off

    <Location "/">
        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE openaerialmap.settings
        PythonPath "['/var/www/oam'] + sys.path"
    </Location>

    <Location "/media">
        SetHandler None
    </Location>

    <Location "/static">
        SetHandler None
    </Location>
    <Location "/map">
        SetHandler None
    </Location>
Alias /media/ /usr/lib/python2.4/site-packages/django/contrib/admin/media/
</VirtualHost>

