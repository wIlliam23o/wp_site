""" Urls for welbornprod sub-apps. """
from django.conf.urls import patterns, include, url
from apps import views as appviews

# Patterns for apps.
urlpatterns = patterns('',
                       # apps index
                       url(r'^/?$', appviews.view_index),
                       # phonewords
                       url(r'^[Pp]hone[Ww]ords/?',
                           include('apps.phonewords.urls')),
                       # paste
                       url(r'^[Pp]aste/?',
                           include('apps.paste.urls')),
                       )
