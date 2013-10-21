from django.http import Http404
from django.views.decorators.csrf import requires_csrf_token

from wp_main.utilities import responses, utilities
from wp_main.utilities.wp_logging import logger
#from misc.models import wp_misc
from misc import tools as misctools

_log = logger('misc').log

@requires_csrf_token
def view_index(request):
    """ Main index for Misc objects. """
    
    miscobjs = misctools.get_visible_objects()
    return responses.clean_response_req("misc/index.html",
                                        {'request': request,
                                         'extra_style_link_list': [utilities.get_browser_style(request),
                                                                   '/static/css/misc.css'],
                                         'miscobjects': miscobjs,
                                         },
                                        with_request=request)
    
@requires_csrf_token
def view_misc_any(request, identifier):
    """ View a specific misc item. """
            
    misc = misctools.get_by_identifier(identifier)
    if not misc:
        # No misc item found by that identifier
        raise Http404()
    
    return responses.clean_response_req('misc/misc.html',
                                        {'request': request,
                                         'extra_style_link_list': [utilities.get_browser_style(request),
                                                                   '/static/css/misc.css'],
                                         'misc': misc,
                                         },
                                        with_request=request)
