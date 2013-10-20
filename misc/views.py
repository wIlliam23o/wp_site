from django.http import Http404

from wp_main.utilities import responses, utilities
from wp_main.utilities.wp_logging import logger
#from misc.models import wp_misc
from misc import tools as misctools

_log = logger('misc').log

def view_index(request):
    """ Main index for Misc objects. """
    
    miscobjs = misctools.get_visible_objects()
    return responses.clean_response("misc/index.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               '/static/css/misc.css'],
                                     'miscobjects': miscobjs,
                                    })
    

def view_misc_any(request, identifier):
    """ View a specific misc item. """
            
    misc = misctools.get_by_identifier(identifier)
    if not misc:
        # No misc item found by that identifier
        raise Http404()
    
    return responses.clean_response('misc/misc.html',
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               '/static/css/misc.css'],
                                     'misc': misc,
                                     })
