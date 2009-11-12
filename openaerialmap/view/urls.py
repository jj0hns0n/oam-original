from django.conf.urls.defaults import *

urlpatterns = patterns('openaerialmap.view.views',
    (r'^generate_mapfile/', 'generate_mapfile'),
    (r'^datasource/(?P<id>[0-9]+)/', 'datasource_info'),
    (r'^$', 'home'),
    (r'^datasource/$', 'datasource_info'),
    (r'^agent/create/', 'agent_create'),
    (r'^agent/edit/(?P<id>[0-9]+)/', 'agent_create'),
    (r'^datasource/create/', 'datasource_create'),
    (r'^datasource/edit/(?P<id>[0-9]+)/', 'datasource_create'),
    (r'^datarecord/create/', 'datarecord_create'),
    (r'^datarecord/edit/(?P<id>[0-9]+)/', 'datarecord_create'),
    (r'^datasource/', 'datasource_info'),
    (r'^attribution/', 'attribution_info'),
)
