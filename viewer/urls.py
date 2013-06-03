from django.conf.urls import patterns, url
from viewer import views

urlpatterns = patterns('',
        # no filename (POST data)
        url(r'^$', views.view_loader),
        # get file contents
        url(r'^/?file/?$', views.ajax_contents),
        # test loader
        #url(r'^/?testload/?$', views.test_loader),
        # Attempted direct access.
        #url(r'^(?P<file_path>.+)$', views.view_loader),
        )