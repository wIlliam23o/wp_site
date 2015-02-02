from django.conf.urls import pattern, url

from img import views
urlpatterns = pattern(
    '',
    # Basic index viewer.
    url(r'^$', views.views_index, name='img_index'),
    # Explicit upload page (probably won't be kept around)
    url(r'^/?upload/?$', views.view_upload, name='img_upload'),
)
