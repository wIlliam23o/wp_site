from django.conf.urls import url

from apps.timekeeper import views
# Patterns for pastebin app.
urlpatterns = [
    # timekeeper main
    url(r'^/?$', views.view_index),
]
