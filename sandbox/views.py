# authentication
from django.contrib import auth
from django.contrib.auth.decorators import login_required
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
#from wp_main.utilities import htmltools
#from projects import tools

# logging
from wp_main.utilities.wp_logging import logger
_log = logger('sandbox').log


def view_index(request):
    if not request.user.is_staff:
        errmsg = '<div>{}</div>'.format(
            '<br>'.join((
                 'The sandbox is for private use.',
                 'You wouldn\'t like it anyway...'))
        )
        return responses.error403(request, user_error=errmsg)
    # Staff. Show the sandbox.
    context = None
    return responses.clean_response("sandbox/index.html", context)
