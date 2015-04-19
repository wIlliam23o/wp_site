import logging
import os.path

# Mark generated Html as safe to view.
from django.utils.safestring import mark_safe
# Gloval settings
from django.conf import settings


# Download tools
from downloads import dltools

# Local Tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
log = logging.getLogger('wp.downloads')


def index(request):
    """ default download page, when no file is specified """

    return download(request, '')


def download(request, file_path):
    """ provides download of files,
        tracks download count of projects and possibly others
        by checking file's project owner, incrementing the count,
        and then redirecting to the actual file.
    """

    # File path may be an incomplete path to the actual location.
    # /cedit/source is just as good as /static/files/cedit/source
    # so we must grab the real (absolute) path, and then convert
    # it to a valid static path.

    # location on disk
    absolute_path = utilities.get_absolute_path(file_path)
    # location relative to site
    if settings.SERVER_LOCATION == 'local':
        static_path = absolute_path.replace(settings.STATIC_PARENT, '')
    else:
        # remote, file is actually located at the static_server dir.
        # but we will need to forward the user to the /static url.
        static_path = absolute_path.replace(settings.STATIC_ROOT, '')
        if static_path.startswith('/'):
            static_path = '/static{}'.format(static_path)
        else:
            static_path = '/static/{}'.format(static_path)

    # used for local only.
    if (not static_path.startswith('/')):
        static_path = '/{}'.format(static_path)

    if not absolute_path:
        # File doesn't exist. Return an error.
        log.debug('file doesn\'t exist: {}'.format(file_path))
        alert_message = 'Sorry, that file doesn\'t exist.'
        main_content = '\n'.join((
            '<div class=\'wp-block\'>',
            '<a href=\'/\'><span>Click here to go home.</span></a>',
            '</div>'
        ))
        context = {
            'request': request,
            'main_content': mark_safe(main_content),
            'alert_message': mark_safe(alert_message),
            'extra_style_link_list':
            [utilities.get_browser_style(request)]
        }
        response = responses.clean_response('home/main.html', context)
    else:
        # redirect to actual file.
        # log.debug("redirecting to: " + static_path)
        response = responses.redirect_response(static_path)
        # File to track? (not a directory)
        if os.path.isfile(absolute_path):
            # see if its a trackable model's file, increment it's count.
            dltools.increment_dl_count(file_path, absolute_path)

    return response
