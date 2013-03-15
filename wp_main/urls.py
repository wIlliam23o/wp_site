#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

# enable the admin:
from django.contrib import admin
admin.autodiscover()

# Main Site (home)
urlpatterns = patterns('',
    url(r'^$', include('home.urls')),
    )

# Projects view (projects)
urlpatterns += patterns('',
    url(r'^[Pp]rojects/?', include('projects.urls'))
    )

# Download view (downloads)
urlpatterns += patterns('',
    # /dl/
    url(r'^[Dd][Ll]/?', include('downloads.urls'))
    )

# Viewer view (viewer)
urlpatterns += patterns('',
    url(r'^[Vv]iew/?', include('viewer.urls'))
    )
# Admin/Other
urlpatterns += patterns('',
    # Examples:
    # url(r'^$', 'wp_main.home.views.index', name='home'),
    # url(r'^wp_main/', include('wp_main.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/?', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/?', include(admin.site.urls)),
    )


