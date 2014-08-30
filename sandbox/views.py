# authentication
from django.contrib import auth
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
#from wp_main.utilities import htmltools
#from projects import tools

# For the staff_required decorator
from functools import wraps

# logging
from wp_main.utilities.wp_logging import logger
_log = logger('sandbox').log


@responses.staff_required(user_error='The sandbox is for private use.')
def view_index(request):
    """ Landing page for the sandbox. Nothing important. """
    context = None
    return responses.clean_response("sandbox/index.html", context)
