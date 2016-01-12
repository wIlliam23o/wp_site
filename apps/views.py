from wp_main.utilities import responses

from apps import tools as apptools


def view_index(request):
    """ Landing page for wp apps listing. """
    context = {
        'apps': apptools.get_apps(admin_apps=request.user.is_staff),
    }
    return responses.clean_response(
        'apps/index.html',
        context=context,
        request=request)
