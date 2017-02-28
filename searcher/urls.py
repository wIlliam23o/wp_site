from django.conf.urls import url
from searcher import views

urlpatterns = [
    # view paged results.
    # must come before view_results url.
    url(r'^[Pp]age/?$', views.view_paged),
    # run search query without GET, display results.
    url(r'^(?P<query>.+)$', views.view_results),
    # no query, show search form.
    url(r'^$', views.view_index),
]
