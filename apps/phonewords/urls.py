from django.conf.urls import url

from apps.phonewords import views
# Patterns for phonewords.
urlpatterns = [
    # phonewords main
    url(r'^/?$', views.view_index),
    url(r'/.+', views.view_index),
]
