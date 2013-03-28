# safe html in responses.
from django.utils.safestring import mark_safe

# various welbornprod tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities import htmltools
# logging
#from wp_main.utilities.wp_logging import logger

def index(request):
    """ serve up main site """
    
    # setup logging
    #_log = logger("welbornprod.home.index", use_file=True)

    # default content for index
    default_content = utilities.get_browser_name(request)

    # render final page
    return responses.clean_response("home/index.html",
                                    {'extra_style_link': utilities.get_browser_style(request),
                                     'default_content': mark_safe(default_content),
                                     })
    

def view_about(request):
    """ return the about page for welbornproductions. """
    
    about_content = htmltools.load_html_file("static/html/about.html")
    return responses.clean_response("home/about.html",
                                    {'extra_style_link': "/static/css/about.css",
                                     'about_content': mark_safe(about_content),
                                     })

