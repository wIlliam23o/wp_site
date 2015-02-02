from django.conf.urls import pattern, url

from img import views
urlpatterns = pattern(
    '',
    # Basic index viewer.
    url(r'^$', views.views_index, name='img_index'),
)
