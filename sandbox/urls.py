from django.conf.urls import patterns, url
from sandbox import views

urlpatterns = patterns(
    '',
    # sandbox index
    url(r'^/?$', views.view_index, name='sandbox'),
)
