""" Urls for welbornprod sub-apps. """
from django.conf.urls import patterns, include, url
from apps import views as appviews

# Patterns for apps.
urlpatterns = patterns('',
                       # index.
                       url(r'^/?$', appviews.view_index),
                       # phonewords
                       url(r'^phonewords', include('apps.phonewords.urls')),
                       )
