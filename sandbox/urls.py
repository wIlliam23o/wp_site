from django.conf.urls import patterns, url
from sandbox import views

urlpatterns = patterns(
    '',
    # sandbox index
    url(r'^/?$', views.view_index, name='sandbox'),
    # alert test.
    url(r'^/alert/?$', views.view_alert, name='sandbox_alert'),
    url(r'^/notice/?$', views.view_notice, name='sandbox_notice'),
)
