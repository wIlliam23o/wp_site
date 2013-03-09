from django.conf.urls import patterns, include, url
from projects import views

urlpatterns = patterns('',
        # projects index
        url(r'^$', views.index, name='projects'),
        # by project ID
        url(r'^(?P<_id>\d+)/?$', views.by_id),
        # by alias
        url(r'^(?P<_alias>[^A-Z,0-9]+)/?$', views.by_alias),
        # by name
        url(r'^(?P<_name>^\w+[ ]?\w+[ ]\w+[ ]?\w+)/?$', views.by_name),
        
                      )