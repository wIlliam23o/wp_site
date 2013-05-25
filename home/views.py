# safe html in responses.
from django.utils.safestring import mark_safe, mark_for_escaping

# various welbornprod tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities import htmltools

# logging
from wp_main.utilities.wp_logging import logger
_log = logger("home").log
############# @todo: make log_context() so context keys/values can be passed to logging!
# Home tools
from home import hometools as htools

def index(request):
    """ serve up main site """
    
    # setup logging
    #_log = logger("welbornprod.home.index", use_file=True)

    # render final page
    return responses.clean_response("home/index.html",
                                    {'request': request,
                                     'blog_post': htools.get_latest_blog(),
                                     'featured_project': htools.get_featured_project(),
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     })
    

def view_about(request):
    """ return the about page for welbornproductions. """
    
    about_content = htmltools.load_html_file("static/html/about.html")
    return responses.clean_response("home/about.html",
                                    {'request': request,
                                     'extra_style_link_list': ["/static/css/about.css",
                                                               utilities.get_browser_style(request)],
                                     'about_content': mark_safe(about_content),
                                     })


def view_debug(request):
    """ return the django debug info page. """
    
    return responses.clean_response("home/debug.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/highlighter.css"],
                                     })

def view_scriptkids(request):
    """ return my script kiddie view 
        (for people trying to access wordpress-login pages and stuff like that.)
    """
    
    # get ip if possible.
    ip_address = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip_address is None: ip_address = request.META.get("REMOTE_ADDR", None)
    use_ip = (ip_address is not None)

    # get insulting image to display
    scriptkid_img = htools.get_scriptkid_image()
    if scriptkid_img is not None: 
        scriptkid_img = utilities.get_relative_path(scriptkid_img)
    use_img = (scriptkid_img is not None)
    
    # return formatted template.
    return responses.clean_response("home/scriptkids.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/highlighter.css"],
                                     'use_img': use_img,
                                     'scriptkid_img': scriptkid_img,
                                     'use_ip': use_ip,
                                     'ip_address':ip_address,
                                     })
    
def view_403(request):
    """ return the forbidden page. (403 template) """
    
    return view_error(request, 403)
    
    
def view_404(request):
    """ return the page not found view (404 template) """
    
    return view_error(request, 404)
    

def view_500(request):
    """ return the internal server error page. """
    
    return view_error(request, 500)

    
def view_error(request, error_number):
    """  returns  appropriate error page when given the error code. """
    
    request_path = request.META["PATH_INFO"]
    if request_path.startswith('/'):
        request_path = request_path[1:]
    
    serror = str(error_number)
    # if its not one of these I don't have a template for it,
    # so it really would be a file-not-found error.
    if not serror in ["403", "404", "500"]:
        serror = "404"
        
    return responses.clean_response("home/" + serror + ".html",
                                    {"request": request,
                                     "request_path": mark_for_escaping(request_path),
                                     "extra_style_link_list": utilities.get_browser_style(request),
                                     })
    