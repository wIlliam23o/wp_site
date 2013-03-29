from django.conf.urls import patterns, url
from searcher import views

urlpatterns = patterns('',
        # run search query, display results.
        url(r'^/?(?P<_query>.+)$', views.view_results),
        # no query, show search form.
        url(r'^/?$', views.view_index),
        )