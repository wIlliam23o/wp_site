from wp_main.utilities import responses, utilities

from apps import tools as apptools


def view_index(request):
    apps = apptools.get_apps()
    context = {
        'request': request,
        'extra_style_link_list': [
            utilities.get_browser_style(request),
            '/static/css/apps.min.css'],
        'apps': apps,
    }

    return responses.clean_response('apps/index.html', context)
