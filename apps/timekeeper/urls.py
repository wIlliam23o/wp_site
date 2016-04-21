from django.conf.urls import patterns, url

from apps.timekeeper import views
# Patterns for pastebin app.
urlpatterns = patterns(
    '',
    # timekeeper main
    url(r'^/?$', views.view_index),
)
