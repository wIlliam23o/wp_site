from wp_main.utilities import responses

from apps import tools as apptools


def view_index(request):
    apps = apptools.get_apps()
    context = {
        'request': request,
        'apps': apps,
    }

    return responses.clean_response('apps/index.html', context)
