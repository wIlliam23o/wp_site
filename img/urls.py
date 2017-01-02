from django.conf.urls import url

from img import views
urlpatterns = [
    # Basic index viewer.
    url(r'^$', views.view_index),
]
