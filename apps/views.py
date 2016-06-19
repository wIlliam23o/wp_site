from wp_main.utilities import responses

from apps import tools as apptools


def view_index(request):
    """ Landing page for wp apps listing. """
    context = {
        'apps': apptools.get_apps(admin_apps=request.user.is_staff),
    }
    if request.user.is_staff:
        context['agenttools'] = {
            'IP': {
                'url': '/ip.html',
                'description': 'Show your user agent IP.',
                'simple_url': '/ip',
            },
            'Text Mode': {
                'url': '/textmode.html',
                'description': 'Show whether your browser is in text mode.',
                'simple_url': '/textmode',
            },
            'User Agent': {
                'url': '/useragent.html',
                'description': 'Show your user agent string.',
                'simple_url': '/ua'
            }
        }
    return responses.clean_response(
        'apps/index.html',
        context=context,
        request=request)
