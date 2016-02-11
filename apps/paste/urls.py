from django.conf.urls import patterns, url

from apps.paste import views
# Patterns for pastebin app.
urlpatterns = patterns(
    '',
    # paste main
    url(r'^$', views.view_index),
    # public api submit
    url(r'^api/submit/?$', views.submit_public),
    # public api
    url(r'^api/?$', views.view_json),
    # paste submit (on site)
    url(r'^submit/?$', views.submit_ajax),
    # paste replies
    url(r'^replies/?$', views.view_replies),
    # latest pastes
    url(r'^latest/?$', views.view_latest),
    # top pastes
    url(r'^top/?$', views.view_top),
    # plain
    url(r'^raw/?$', views.view_paste_raw),
)
