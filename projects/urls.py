from django.conf.urls import patterns, url
from projects import views

urlpatterns = patterns(
    '',
    # projects index
    url(r'^$', views.view_index, name='projects'),
    # individual project page (by id, alias, or name.)
    url(r'^(?P<identifier>[^/]+)', views.request_any),
)
