from django.conf.urls import patterns, url

from apps.paste import views
# Patterns for pastebin app.
urlpatterns = patterns('',
                       # paste main
                       url(r'^$', views.view_index),
                       # paste submit
                       url(r'submit/?', views.ajax_submit),
                       # paste replies
                       url(r'replies/?', views.view_replies),
                       # latest pastes
                       url(r'latest/?', views.view_latest),
                       # top pastes
                       url(r'top/?', views.view_top),
                       # public api
                       url(r'api/?', views.view_json),
                       )
