# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
# login url is set in settings
from django.conf import settings
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
                       url(r'^404\.html$',
                           homeviews.view_404),
                       # 403 tester
                       url(r'^403\.html$',
                           homeviews.view_403),
                       # 500 tester
                       url(r'^500\.html$',
                           homeviews.view_500),
                       # debug info
                       url(r'^debug\.html$',
                           homeviews.view_debug),
                       # ip simple
                       url(r'^ip$',
                           homeviews.view_ip_simple),
                       # ip html
                       url(r'^ip\.html?$',
                           homeviews.view_ip),
                       # stats info
                       url(r'^stats\.html$',
                           homeviews.view_stats),
                       # test page (random code tests for actual server)
                       url(r'^test\.html$',
                           homeviews.view_test),
                       # login processor
                       url(settings.LOGIN_URL_REGEX,
                           'django.contrib.auth.views.login'),
                       # bad login message
                       url(r'^badlogin\.html$',
                           homeviews.view_badlogin),
                       # robots.txt server
                       url(r'^robots\.txt$',
                           robots.view_byserver),
                       # sitemap server
                       url(r'^sitemap\.xml$',
                           sitemaps.view_byserver),
                       # home (index)
                       url(r'^$',
                           homeviews.index),
                       # about page
                       url(r'^[Aa]bout/?$',
                           homeviews.view_about),
                       )

# Apps views (apps) (see apps.urls)
urlpatterns += patterns('',
                        url(r'^[Aa]pps/?',
                            include('apps.urls')),
                        # shortcut for /apps/paste
                        url(r'^[Pp]aste/?',
                            include('apps.paste.urls')),
                        )

# Projects view (projects)
urlpatterns += patterns('',
                        url(r'^[Pp]rojects/?',
                            include('projects.urls'))
                        )

# Misc view (misc)
urlpatterns += patterns('',
                        url(r'^[Mm]isc/?',
                            include('misc.urls'))
                        )
# Download view (downloads)
urlpatterns += patterns('',
                        # /dl/
                        url(r'^[Dd][Ll]/?',
                            include('downloads.urls'))
                        )

# Viewer view (viewer)
urlpatterns += patterns('',
                        url(r'^[Vv]iew/?',
                            include('viewer.urls'))
                        )

# Blogger views (blogger)
urlpatterns += patterns('',
                        url(r'[Bb]log/?',
                            include('blogger.urls'))
                        )

# Searcher views (searcher)
urlpatterns += patterns('',
                        url(r'[Ss]earch/?',
                            include('searcher.urls'))
                        )

# Admin/Other
urlpatterns += patterns('',
                        # Examples:
                        # url(r'^$', 'wp_main.home.views.index', name='home'),
                        # url(r'^wp_main/', include('wp_main.foo.urls')),

                        # Uncomment the admin/doc line below
                        # to enable admin documentation:
                        url(r'^admin/doc/?',
                            include('django.contrib.admindocs.urls')),

                        # Uncomment the next line to enable the admin:
                        url(r'^admin/?',
                            include(admin.site.urls)),
                        )

# Error handlers
handler404 = 'home.views.view_404'
handler403 = 'home.views.view_403'
handler500 = 'home.views.view_500'

# Script Kiddie attempts
# (not sure what to do right now except show
#  them a msg stating how dumb they are.)
urlpatterns += patterns('',
                        # wordpress login
                        url(r'^wp\-login\.php$',
                            homeviews.view_scriptkids),
                        url(r'^administrator/index\.php$',
                            homeviews.view_scriptkids),
                        url(r'^admin\.php$',
                            homeviews.view_scriptkids),
                        )
