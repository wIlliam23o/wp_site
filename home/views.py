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
from wp_main.utilities import tweets
from scripts import wpstats

# logging
from wp_main.utilities.wp_logging import logger
_log = logger("home").log
# @todo: make log_context() so context keys/values can be passed to logging!
# Home tools
from home import hometools
from home.models import home_config
homeconfig = home_config.objects.get()


def convert_line(line):
    """ Format a single line for stats info. """
    return mark_safe('{}\n<br>\n'.format(line.replace(' ', '&nbsp;')))


def convert_pblock(pblock):
    """ Format a print_block() for stats info. """
    if not pblock:
        return []
    pblock_args = {'append_key': ': '}
    return [convert_line(line) for line in pblock.iterblock(**pblock_args)]


def index(request):
    """ serve up main page (home, index, landing) """
    # Get latest tweet (if available.)
    if homeconfig.show_latest_tweet:
        latest_tweets = tweets.get_tweets('cjwelborn', count=1)
        latest_tweet = latest_tweets[0] if latest_tweets else None
    else:
        latest_tweet = None

    # render main page
    context = {
        'request': request,
        'blog_post': hometools.get_latest_blog(),
        'featured_project': hometools.get_featured_project(),
        'featured_app': hometools.get_featured_app(),
        'latest_tweet': latest_tweet,
        'extra_style_link_list': [utilities.get_browser_style(request)],
    }
    return responses.clean_response('home/index.html', context)


def makestats(name, getfunc, orderby=None):
    """ Create a StatsInfo() object from a name, get_info_func, and orderby
        Arguments:
            name     : Name to display for these stats.
            getfunc  : Function that returns a print_block() with the stats.
            orderby  : Sort order for the objects gathered.
                       Defaults to: -download_count
    """

    if not orderby:
        orderby = '-download_count'
    oinfo = getfunc(orderby=orderby)
    return wpstats.StatsInfo(name, convert_pblock(oinfo))


def view_403(request):
    """ return the forbidden page. (403 template) """
    return view_error(request, 403)


def view_404(request):
    """ return the page not found view (404 template) """
    return view_error(request, 404)


def view_500(request):
    """ return the internal server error page. """
    return view_error(request, 500)


def view_about(request):
    """ return the about page for welbornproductions. """

    # Pass link list for the about page
    context = {
        'request': request,
        'extra_style_link_list': [
            '/static/css/about.min.css',
            utilities.get_browser_style(request)],
    }
    return responses.clean_response('home/about.html', context,
                                    link_list=htmltools.auto_link_list,
                                    auto_link_args={'target': '_blank'}
                                    )


def view_badlogin(request):
    """ show the bad login message """

    context = {
        'request': request,
        'extra_style_link_list': [utilities.get_browser_style(request)],
    }
    return responses.clean_response('home/badlogin.html', context)


@login_required(login_url='/login')
def view_debug(request):
    """ return the django debug info page. """
    siteversion = settings.SITE_VERSION
    context = {
        'request': request,
        'djangoversion': get_django_version(),
        'sysversion': sysversion,
        'siteversion': siteversion,
        'extra_style_link_list': [
        utilities.get_browser_style(request),
        '/static/css/highlighter.min.css'],
    }
    return responses.clean_response('home/debug.html', context)


def view_error(request, error_number):
    """  returns  appropriate error page when given the error code. """

    request_path = request.META['PATH_INFO']
    if request_path.startswith('/'):
        request_path = request_path[1:]

    serror = str(error_number)
    # if its not one of these I don't have a template for it,
    # so it really would be a file-not-found error.
    if not serror in ['403', '404', '500']:
        serror = '404'
    context = {
        'request': request,
        'request_path': mark_for_escaping(request_path),
        'extra_style_link_list': [utilities.get_browser_style(request)],
    }
    return responses.clean_response_req('home/{}.html'.format(serror),
                                        context,
                                        request=request)


def view_ip(request):
    """  returns the remote ip page. """
    context = {
        'request': request,
        'extra_style_link_list': [utilities.get_browser_style(request)],
    }
    return responses.clean_response('home/ip.html', context)


def view_ip_simple(request):
    """ returns the remote ip in plain text. """
    ip = '{}\n'.format(utilities.get_remote_ip(request))
    return responses.text_response(ip)


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
                referer_view = responses.get_referer_view(request,
                                                          default=None)

                #_log.debug("referer_view: " + str(referer_view))

                # Change response based on whether or not prev. view was given.
                if referer_view is None:
                    # Success
                    response = responses.redirect_response('/')
                else:
                    # Previous view
                    response = responses.redirect_response(referer_view)

    return response


def view_scriptkids(request):
    """ return my script kiddie view
        (for people trying to access wordpress-login pages and stuff like that.)
    """

    # get ip if possible.
    #ip_address = request.META.get("HTTP_X_FORWARDED_FOR", None)
    # if ip_address is None:
    #    ip_address = request.META.get("REMOTE_ADDR", None)
    ip_address = utilities.get_remote_ip(request)
    use_ip = (ip_address is not None)
    try:
        path = request.path
    except AttributeError:
        path = '<error getting path>'
    _log.error('ScriptKid Access from: {} -> {}'.format(ip_address, path))

    # get insulting image to display
    scriptkid_img = hometools.get_scriptkid_image()
    if scriptkid_img is not None:
        scriptkid_img = utilities.get_relative_path(scriptkid_img)
    use_img = (scriptkid_img is not None)

    context = {
        'request': request,
        'extra_style_link_list': [
            utilities.get_browser_style(request),
            '/static/css/highlighter.min.css'],
        'use_img': use_img,
        'scriptkid_img': scriptkid_img,
        'use_ip': use_ip,
        'ip_address': ip_address,
    }
    # return formatted template.
    return responses.clean_response('home/scriptkids.html', context)


@login_required(login_url='/login')
def view_stats(request):
    """ return stats info for projects, blog posts, and file trackers.
        should require admin permissions.
    """

    if request.user.is_authenticated():
        # gather print_block stats from wpstats and convert to lists of strings.
        # for projects, misc objects, blog posts, and file trackers...
        projectinfo = makestats('Project', wpstats.get_projects_info)
        miscinfo = makestats('Misc', wpstats.get_misc_info)
        postinfo = makestats('Posts', wpstats.get_blogs_info, '-view_count')
        fileinfo = makestats('File Trackers', wpstats.get_files_info)

        # Add them to a collection.
        stats = wpstats.StatsCollection(projectinfo,
                                        miscinfo,
                                        postinfo,
                                        fileinfo)
        # Build template variables...
        context = {
            'request': request,
            'extra_style_link_list': [
                utilities.get_browser_style(request),
                '/static/css/stats.min.css'],
            'stats': stats,
        }
        return responses.clean_response('home/stats.html', context)

    # Not authenticated, return the bad login page. No stats for you!
    context = {
        'request': request,
        'extra_style_link_list': [utilities.get_browser_style(request)],
    }
    return responses.clean_response('home/badlogin.html', context)


def view_raiseerror(request):
    """ Purposely raise an error while loading this view, for testing.
        Custom error msgs can be passed as GET arguments.
    """

    reqargs = responses.get_request_args(request)
    if reqargs['msgs']:
        msgs = reqargs['msgs'].split('|')
    else:
        msgs = None
    return responses.error500(request, msgs=msgs)
