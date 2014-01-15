# Version info
from sys import version as sysversion
from django.utils.version import get_version as get_django_version
from django.conf import settings

# safe html in responses.
from django.utils.safestring import mark_safe, mark_for_escaping
# authentication
from django.contrib import auth
from django.contrib.auth.decorators import login_required
# various welbornprod tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities import htmltools
from scripts import wpstats

# logging
from wp_main.utilities.wp_logging import logger
_log = logger("home").log
# @todo: make log_context() so context keys/values can be passed to logging!
# Home tools
from home import hometools as htools


def index(request):
    """ serve up main page (home, index, landing) """

    # render main page
    return responses.clean_response("home/index.html",
                                    {'request': request,
                                     'blog_post': htools.get_latest_blog(),
                                     'featured_project': htools.get_featured_project(),  # noqa
                                     'extra_style_link_list':
                                         [utilities.get_browser_style(request),
                                         ],
                                     })
    

def view_about(request):
    """ return the about page for welbornproductions. """
    
    # Pass link list for the about page

    return responses.clean_response("home/about.html",
                                    {'request': request,
                                     'extra_style_link_list': ["/static/css/about.min.css",
                                                               utilities.get_browser_style(request)],
                                     },
                                    link_list=htmltools.auto_link_list,
                                    auto_link_args={"target": "_blank"}
                                    )


@login_required(login_url='/login')
def view_debug(request):
    """ return the django debug info page. """
    siteversion = settings.SITE_VERSION
    
    return responses.clean_response("home/debug.html",
                                    {'request': request,
                                     'djangoversion': get_django_version(),
                                     'sysversion': sysversion,
                                     'siteversion': siteversion,
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/highlighter.min.css"],
                                     })


def view_ip(request):
    """  returns the remote ip page. """
    
    return responses.clean_response('home/ip.html',
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     })


def view_ip_simple(request):
    """ returns the remote ip in plain text. """
    
    return responses.text_response('{}\n'.format(str(utilities.get_remote_ip(request))))


@login_required(login_url='/login')
def view_test(request):
    """ returns whatever tests are being conducted in test.html template. """
    
    return responses.clean_response("home/test.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     })


def view_login(request):
    """ processes login attempts ## NOT BEING USED RIGHT NOW ##"""
    
    # My first attempt at a login page, not very good.
    # I am using Django's auth.views with modified css right now.
    # maybe in the future I can do this right.
    
    username = request.REQUEST.get('user', None)
    pw = request.REQUEST.get('pw', None)
    
    #_log.debug("username: " + str(username) + ", pw: " + str(pw))
    
    response = responses.redirect_response("/badlogin.html")
    if (username is not None) and (pw is not None):
        
        user = auth.authenticate(user=username, password=pw)
       
        #_log.debug("USER=" + str(user))
        
        if user is not None:
            if user.is_active():
                auth.login(request, user)
                referer_view = responses.get_referer_view(request, default=None)
                
                #_log.debug("referer_view: " + str(referer_view))
                
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
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     })


@login_required(login_url="/login")
def view_stats(request):
    """ return stats info for projects, blog posts, and file trackers.
        should require admin permissions.
    """
    
    def convert_line(line):
        return mark_safe(line.replace(' ', '&nbsp;') + '\n<br/>\n')

    def convert_pblock(pblock):
        if pblock is None:
            return []
        if not pblock.keys():
            return []
    
        pblock_args = {'append_key': ': '}
        return [convert_line(line) for line in pblock.iterblock(**pblock_args)]
    # gather print_block stats from wpstats and convert to lists of strings.
    # for projects, misc objects, blog posts, and file trackers...
    projectinfo = htools.StatsInfo('Projects', convert_pblock(wpstats.get_projects_info(orderby='-download_count')))
    miscinfo = htools.StatsInfo('Misc', convert_pblock(wpstats.get_misc_info(orderby='-download_count')))
    postinfo = htools.StatsInfo('Posts', convert_pblock(wpstats.get_blogs_info(orderby='-view_count')))
    fileinfo = htools.StatsInfo('File Trackers', convert_pblock(wpstats.get_files_info(orderby='-download_count')))
    # Add them to a collection.
    stats = htools.StatsCollection(projectinfo, miscinfo, postinfo, fileinfo)
    
    if request.user.is_authenticated():
        response = responses.clean_response("home/stats.html",
                                            {'request': request,
                                             'extra_style_link_list': [utilities.get_browser_style(request),
                                                                       "/static/css/stats.min.css"],
                                             'stats': stats,
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
    if ip_address is None:
        ip_address = request.META.get("REMOTE_ADDR", None)
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
                                                               "/static/css/highlighter.min.css"],
                                     'use_img': use_img,
                                     'scriptkid_img': scriptkid_img,
                                     'use_ip': use_ip,
                                     'ip_address': ip_address,
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
                                     "extra_style_link_list": [utilities.get_browser_style(request)],
                                     })
