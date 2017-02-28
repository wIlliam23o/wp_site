from django.conf.urls import url
from projects import views

urlpatterns = [
    # projects index
    url(r'^$', views.view_index, name='projects'),
    # individual project page (by id, alias, or name.)
    url(r'^(?P<identifier>[^/]+)', views.request_any),
]
