from django.conf.urls import patterns, include, url
from downloads import views

urlpatterns = patterns('',
        # send filename to downloader
        url(r'^$/?', views.index),
        url(r'^(?P<file_path>.+)', views.download),
        )
