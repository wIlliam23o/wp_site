from wp_main.utilities import responses, utilities

from apps import tools as apptools


def view_index(request):
    appsinfo = apptools.get_apps()
    return responses.clean_response('apps/index.html',
                                    {'request': request,
                                     'extra_style_link_list':
                                        [utilities.get_browser_style(request),
                                         '/static/css/apps.min.css'],
                                     'appsinfo': appsinfo,
                                     })
