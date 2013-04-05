#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

# main views
from home import views as homeviews
# get sitemaps
from wp_main.sitemaps.main import view_sitemap

# enable the admin:
from django.contrib import admin
admin.autodiscover()

# Main Site (home)
urlpatterns = patterns('',
    # sitemap server
    url(r'^sitemap\.xml$',view_sitemap),
    # home (index)
    url(r'^$', homeviews.index),
    # about page
    url(r'^[Aa]bout/?$', homeviews.view_about),
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

# Blogger views (blogger)
urlpatterns += patterns('',
    url(r'[Bb]log/?', include('blogger.urls'))
    )

# Searcher views (searcher)
urlpatterns += patterns('',
    url(r'[Ss]earch/?', include('searcher.urls'))
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


