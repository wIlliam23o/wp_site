'''
    Welborn Productions - Misc - URLS
    Url Handlers for misc app.
Created on Oct 20, 2013

@author: Christopher Welborn
'''

from django.conf.urls import patterns, url
from misc import views as miscviews

urlpatterns = patterns(
    '',
    # misc index
    url(r'^/?$', miscviews.view_index),
    # specific misc item
    url(r'/(?P<identifier>.+/?)', miscviews.view_misc_any),
)
