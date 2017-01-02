from django.conf.urls import url
from viewer import views

urlpatterns = [
    # no filename (POST data)
    url(r'^$', views.view_loader),
    # get file contents
    url(r'^file/?$', views.ajax_contents),
]
