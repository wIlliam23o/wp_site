from wp_main.utilities import responses, utilities

from misc import tools


def view_index(request):
    """ Main index for Misc objects. """
    
    miscobjs = tools.get_visible_objects()
    return responses.clean_response("misc/index.html",
                                    {'request': request,
                                     'style_link_list': [utilities.get_browser_style()],
                                     'miscobjects': miscobjs,
                                     })
    

def view_misc_any(request, identifier):
    """ View a specific misc item. """
    
    misc = tools.get_by_identifier(identifier)
    return responses.clean_response('misc/misc.html',
                                    {'request': request,
                                     'style_link_list': [utilities.get_browser_style()],
                                     'misc': misc,
                                     })
