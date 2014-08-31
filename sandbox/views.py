# authentication
from django.contrib import auth
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses

# logging
from wp_main.utilities.wp_logging import logger
_log = logger('sandbox').log


@responses.staff_required(user_error='The sandbox is for private use.')
def view_index(request):
    """ Landing page for the sandbox. Nothing important. """
    context = None
    return responses.clean_response("sandbox/index.html", context)
