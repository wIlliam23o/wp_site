from django.conf.urls import patterns, url
from downloads import views

urlpatterns = patterns(
    '',
    # send filename to downloader
    url(r'^$', views.index),
    url(r'^(?P<file_path>.+)', views.download),
)
