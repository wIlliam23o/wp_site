# -*- coding: utf-8 -*-

from django.conf.urls import include, url
# simple redirect urls.
from django.views.generic.base import RedirectView
# login url is set in settings
from django.conf import settings
# login views.
from django.contrib.auth import views as auth_views

# main views
from home import views as homeviews
from home.admin import admin_site

# get sitemaps
from wp_main.sitemaps import sitemaps
# get robots.txt
from wp_main.robots import robots

# Main Site (home)
urlpatterns = [
    # No common prefix for these.
    # 404 tester
    url(
        r'^404\.html?$',
        homeviews.view_404
    ),
    # 403 tester
    url(
        r'^403\.html?$',
        homeviews.view_403
    ),
    # 500 tester
    url(
        r'^500\.html?$',
        homeviews.view_500
    ),
    # error raiser (for testing)
    url(
        r'^raise.html?$',
        homeviews.view_raiseerror
    ),
    # error raiser (for testing)
    url(
        r'^[Rr]aise$',
        homeviews.view_raiseerror
    ),
    # debug info
    url(
        r'^debug\.html?$',
        homeviews.view_debug
    ),
    # ip simple
    url(
        r'^ip/?$',
        homeviews.view_ip_simple
    ),
    # ip html
    url(
        r'^ip\.html?$',
        homeviews.view_ip
    ),
    # login processor
    url(settings.LOGIN_URL_REGEX,
        auth_views.login),
    # bad login message
    url(
        r'^badlogin\.html?$',
        homeviews.view_badlogin
    ),
    # robots.txt server
    url(
        r'^robots\.txt$',
        robots.view_byserver
    ),
    # sitemap server
    url(
        r'^sitemap\.xml$',
        sitemaps.view_byserver
    ),
    # textmode test
    url(
        r'^[Tt]ext[Mm]ode$',
        homeviews.view_textmode_simple
    ),
    url(
        r'^[Tt]ext[Mm]ode\.html?$',
        homeviews.view_textmode
    ),
    # useragent simple
    url(
        r'^[Uu]ser[Aa]gent/?$',
        homeviews.view_useragent_simple
    ),
    # useragent simple
    url(
        r'^[Uu][Aa]/?$',
        homeviews.view_useragent_simple
    ),
    # useragent html
    url(
        r'^[Uu]ser[Aa]gent\.html?$',
        homeviews.view_useragent
    ),
    # useragent html
    url(
        r'^[Uu][Aa]\.html?$',
        homeviews.view_useragent
    ),
    # home (index)
    url(
        r'^$',
        homeviews.index
    ),
    # about page
    url(
        r'^[Aa]bout/?$',
        homeviews.view_about
    ),
]

# Apps views (apps) (see apps.urls)
urlpatterns.extend((
    url(
        r'^[Aa]pps/?',
        include('apps.urls')
    ),
    # shortcut for /apps/paste
    url(
        r'^[Pp]aste/?',
        include('apps.paste.urls')
    ),
))

# Image share
urlpatterns.extend((
    url(
        r'^[Ii][Mm][Gg]/?',
        include('img.urls')
    ),
))

# Projects view (projects)
urlpatterns.extend((
    url(
        r'^[Pp]rojects/?',
        include('projects.urls')
    ),
))

# Misc view (misc)
urlpatterns.extend((
    url(
        r'^[Mm]isc/?',
        include('misc.urls')
    ),
))
# Download view (downloads)
urlpatterns.extend((
    # /dl/
    url(
        r'^[Dd][Ll]/?',
        include('downloads.urls')
    ),

))
# Viewer view (viewer)
urlpatterns.extend((
    url(
        r'^[Vv]iew/?',
        include('viewer.urls')
    ),
))

# Blogger views (blogger)
urlpatterns.extend((
    url(
        r'^[Bb]log/?',
        include('blogger.urls')
    ),
))

# Searcher views (searcher)
urlpatterns.extend((
    url(
        r'^[Ss]earch/?',
        include('searcher.urls')
    ),
))

# Private Sandbox views.
urlpatterns.extend((
    url(
        r'^[Ss]and[Bb]ox/?',
        include('sandbox.urls')
    ),
))

# Stats views.
urlpatterns.extend((
    # stats info
    url(
        r'^[Ss]tats/?',
        include('stats.urls')
    ),
))
# Admin/Other
urlpatterns.extend((
    # Admin docs.
    url(
        r'^admin/doc/?',
        include('django.contrib.admindocs.urls')
    ),

    # Default admin site.
    url(
        r'^admin/?',
        include(admin_site.urls)
    ),
))

# Error handlers
handler404 = 'home.views.view_404'
handler403 = 'home.views.view_403'
handler500 = 'home.views.view_500'

# Script Kiddie attempts
# (not sure what to do right now except show
#  them a msg stating how dumb they are.)
urlpatterns.extend((
    # wordpress login
    url(
        r'^wp-admin',
        homeviews.view_scriptkids
    ),
    url(
        r'^wordpress/wp-admin/?$',
        homeviews.view_scriptkids
    ),
    url(
        r'^wp\-login\.php$',
        homeviews.view_scriptkids
    ),
    url(
        r'^administrator/index\.php$',
        homeviews.view_scriptkids
    ),
    url(
        r'^admin\.php$',
        homeviews.view_scriptkids
    ),
))

# URL Junk (from base64 encoded links)
# These don't get decoded for bots without javascript, so they end up here.
urlpatterns.extend((
    # mailto: cj...
    url(
        r'^bWFpbHRvOmNqQHdlbGJvcm5wcm9kLmNvbQ==',
        homeviews.view_no_javascript
    ),
))

# Simple redirects
urlpatterns.extend((
    url(
        r'^favicon\.ico$',
        RedirectView.as_view(
            url='/static/images/favicons/favicon.ico',
            permanent=True
        )
    ),
))

# Debug toolbar explicit setup (per new debug_toolbar version)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls))
    )
