from django.conf.urls import url
from downloads import views

urlpatterns = [
    # send filename to downloader
    url(r'^$', views.index),
    url(r'^(?P<file_path>.+)', views.download),
]
