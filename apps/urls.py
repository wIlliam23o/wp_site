""" Urls for welbornprod sub-apps. """
from django.conf.urls import include, url
from apps import views as appviews

# Patterns for apps.
urlpatterns = [
    # apps index
    url(
        r'^$',
        appviews.view_index),
    # phonewords
    url(
        r'^[Pp]hone[Ww]ords/?',
        include('apps.phonewords.urls')),
    # paste
    url(
        r'^[Pp]aste/?',
        include('apps.paste.urls')),
    # timekeeper
    url(
        r'^[Tt]ime[Kk]eep(er)?/?',
        include('apps.timekeeper.urls'))
]
