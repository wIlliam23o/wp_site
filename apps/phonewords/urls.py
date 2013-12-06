from django.conf.urls import patterns, url

from apps.phonewords import views
# Patterns for phonewords.
urlpatterns = patterns('',
                       # phonewords main
                       url(r'.+', views.view_index),
                       )
