from django.http import Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page

from wp_main.utilities import responses, utilities
from wp_main.utilities.wp_logging import logger
#from misc.models import wp_misc
from misc import tools as misctools

_log = logger('misc').log


@cache_page(15 * 60)
@csrf_protect
def view_index(request):
    """ Main index for Misc objects. """
    
    miscobjs = misctools.get_visible_objects()
    context = {'request': request,
               'extra_style_link_list': [utilities.get_browser_style(request),
                                         '/static/css/misc.min.css',
                                         '/static/css/highlighter.min.css'],
               'miscobjects': miscobjs,
               }
    return responses.clean_response_req("misc/index.html",
                                        context,
                                        request=request)
    

@cache_page(15 * 60)
@csrf_protect
def view_misc_any(request, identifier):
    """ View a specific misc item. """
            
    misc = misctools.get_by_identifier(identifier)
    if not misc:
        # No misc item found by that identifier
        raise Http404()
    context = {'request': request,
               'extra_style_link_list': [utilities.get_browser_style(request),
                                         '/static/css/misc.min.css',
                                         '/static/css/highlighter.min.css'],
               'misc': misc,
               }
    return responses.clean_response_req('misc/misc.html',
                                        context,
                                        request=request)
