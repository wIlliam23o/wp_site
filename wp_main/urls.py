# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

# main views
from home import views as homeviews
# get sitemaps
from wp_main.sitemaps import sitemaps
# get robots.txt
from wp_main.robots import robots
# enable the admin:
from django.contrib import admin
admin.autodiscover()

# Main Site (home)
urlpatterns = patterns('',
    # 404 tester
    url(r'^404\-test\.html$', homeviews.view_404),
    # 403 tester
    url(r'^403\-test\.html$', homeviews.view_403),
    # 500 tester
    url(r'^500\-test\.html$', homeviews.view_500),
    # debug info
    url(r'^debug\.html$', homeviews.view_debug),
    # robots.txt server
    url(r'^robots\.txt$', robots.view_byserver),
    # sitemap server
    url(r'^sitemap\.xml$',sitemaps.view_byserver),
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

# Error handlers
handler404 = 'home.views.view_404'
handler403 = 'home.views.view_403'
handler500 = 'home.views.view_500'