# safe html in responses.
from django.utils.safestring import mark_safe

# various welbornprod tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities import htmltools
# logging
#from wp_main.utilities.wp_logging import logger
# Home tools
from home import hometools as htools

def index(request):
    """ serve up main site """
    
    # setup logging
    #_log = logger("welbornprod.home.index", use_file=True)

    # render final page
    return responses.clean_response("home/index.html",
                                    {'blog_post': htools.get_latest_blog(),
                                     'featured_project': htools.get_featured_project(),
                                     'extra_style_link': utilities.get_browser_style(request),
                                     })
    

def view_about(request):
    """ return the about page for welbornproductions. """
    
    about_content = htmltools.load_html_file("static/html/about.html")
    return responses.clean_response("home/about.html",
                                    {'extra_style_link': "/static/css/about.css",
                                     'about_content': mark_safe(about_content),
                                     })

