from django.conf.urls import patterns, url
from blogger import views

urlpatterns = patterns(
    '',
    # projects index
    url(r'^/?$', views.index, name='blogger'),
    # no identifier specified
    url(r'^/[Vv]iew/?$', views.no_identifier),
    # view all tags/categories
    url(r'^/[Tt]ags/?$', views.view_tags),
    # view posts with tags
    # must come before view_tag url.
    url(r'^/[Tt]ag/?[Pp]age/(?P<_tag>.+)/?', views.tag_page),
    url(r'^/[Tt]ag/(?P<_tag>.+)/?$', views.view_tag),
    # send identifier to blogger.views.view_post
    url(r'^/[Vv]iew/(?P<_identifier>.+)/?$', views.view_post),
    # pagination view
    url(r'^/[Pp]age/?', views.index_page)
)
