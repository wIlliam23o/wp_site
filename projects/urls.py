from django.conf.urls import patterns, url
from projects import views

urlpatterns = patterns('',
        # projects index
        url(r'^$', views.index, name='projects'),
        # by project ID
        url(r'^(?P<_identifier>\d+)/?$', views.request_any),
        # by alias
        url(r'^(?P<_identifier>[a-z][^0-9][^ ]+)/?$', views.request_any),
        # by name
        url(r'^(?P<_identifier>([A-Z,a-z, ]+)+(\d(\.\d){2})?)/?$', views.request_any),
        
        )