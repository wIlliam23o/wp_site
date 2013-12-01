""" Urls for welbornprod sub-apps. """
from django.conf.urls import patterns, include, url

# Patterns for apps.
urlpatterns = patterns('',
                       # phonewords
                       url(r'^phonewords', include('apps.phonewords.urls')),
                       )
