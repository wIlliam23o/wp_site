from django.conf.urls import patterns, url
from viewer import views

urlpatterns = patterns('',
        # no filename
        url(r'^$/?', views.index),
        # send filename to downloader
        url(r'^(?P<file_path>.+)$', views.viewer),
        )