# safe html in responses.
from django.utils.safestring import mark_safe, mark_for_escaping
# authentication
from django.contrib import auth
from django.contrib.auth.decorators import login_required
# various welbornprod tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities import htmltools
import wpstats

# logging
from wp_main.utilities.wp_logging import logger
_log = logger("home").log
############# @todo: make log_context() so context keys/values can be passed to logging!
# Home tools
from home import hometools as htools

def index(request):
    """ serve up main page (home, index, landing) """

    # render main page
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

@login_required(login_url='/login')
def view_debug(request):
    """ return the django debug info page. """
    
    return responses.clean_response("home/debug.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/highlighter.css"],
                                     })

def view_login(request):
    """ processes login attempts ## NOT BEING USED RIGHT NOW ##"""
    
    # My first attempt at a login page, not very good.
    # I am using Django's auth.views with modified css right now.
    # maybe in the future I can do this right.
    
    username = request.REQUEST.get('user', None)
    pw = request.REQUEST.get('pw', None)
    
    _log.debug("username: " + str(username) + ", pw: " + str(pw))
    
    response = responses.redirect_response("/badlogin.html")
    if (username is not None) and (pw is not None):
        
        user = auth.authenticate(user=username, password=pw)
       
        _log.debug("USER=" + str(user))
        
        if user is not None:
            if user.is_active():
                auth.login(request, user)
                referer_view = responses.get_referer_view(request, default=None)
                
                _log.debug("referer_view: " + str(referer_view))
                
                # Change response based on whether or not previous view was given.
                if referer_view is None:
                    # Success
                    response = responses.redirect_response("/")
                else:
                    # Previous view
                    response = responses.redirect_response(referer_view)

    return response
    

def view_badlogin(request):
    """ show the bad login message """
    
    return responses.clean_response("home/badlogin.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request)]})

@login_required(login_url="/login")
def view_stats(request):
    """ return stats info for projects, blog posts, and file trackers.
        should require admin permissions.
    """
    
    def convert_line(line):
        return mark_safe(line.replace(' ', '&nbsp;') + '\n<br/>\n')
    def convert_pblock(pblock):
        if pblock is None: return []
        pblock_args = {'append_key': ': '}
        return [convert_line(line) for line in pblock.iterblock(**pblock_args)]
    # gather print_block stats from wpstats and convert to lists of strings.
    # for projects, blog posts, and file trackers...
    projectlines = convert_pblock(wpstats.get_projects_info(orderby='-download_count'))
    postlines = convert_pblock(wpstats.get_blogs_info(orderby='-view_count'))
    filelines = convert_pblock(wpstats.get_files_info(orderby='-download_count'))
    
    if request.user.is_authenticated():
        response = responses.clean_response("home/stats.html",
                                            {'request': request,
                                             'extra_style_link_list': [utilities.get_browser_style(request),
                                                                       "/static/css/stats.css"],
                                             'projects': projectlines,
                                             'posts': postlines,
                                             'files': filelines,
                                             })
    else:
        response = responses.clean_response("home/badlogin.html",
                                            {'request': request,
                                             'extra_style_link_list': [utilities.get_browser_style(request)]})
    
    return response


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
    