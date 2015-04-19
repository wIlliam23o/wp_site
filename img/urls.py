from django.conf.urls import patterns, url

from img import views
urlpatterns = patterns(
    '',
    # Basic index viewer.
    url(r'^$', views.view_index),
)
