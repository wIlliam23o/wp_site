import logging
# Version info
from django.utils.version import get_version as get_django_version
from django.conf import settings

# safe html in responses.
from django.utils.safestring import mark_for_escaping
# authentication
from django.contrib import auth
from django.contrib.auth.decorators import login_required

# disable cache for ip/useragent pages.
from django.views.decorators.cache import never_cache

# various welbornprod tools
from wp_main.utilities import (
    utilities,
    responses,
    htmltools,
    tweets
)

# logging
log = logging.getLogger('wp.home')

# Home tools
from home import hometools
from home.models import home_config


def index(request):
    """ Serve up main page (home, index, landing) """
    # Grab config on every request, to keep it fresh without restarting.
    homeconfig = home_config.objects.get()

    # Get latest tweet (if available.)
    if homeconfig.show_latest_tweet:
        latest_tweets = tweets.get_tweets('cjwelborn', count=1)
        latest_tweet = latest_tweets[0] if latest_tweets else None
    else:
        latest_tweet = None

    # render main page
    context = {
        'request': request,
        'featured_blog_post': hometools.get_featured_blog(homeconfig),
        'featured_project': hometools.get_featured_project(homeconfig),
        'featured_app': hometools.get_featured_app(homeconfig),
        'welcome_message': homeconfig.welcome_message,
        'latest_tweet': latest_tweet,
    }
    return responses.clean_response('home/index.html', context)


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
    }
    return responses.clean_response(
        'home/about.html',
        context,
        link_list=htmltools.auto_link_list,
        auto_link_args={'target': '_blank'}
    )


def view_badlogin(request):
    """ show the bad login message """

    context = {
        'request': request,
    }
    return responses.clean_response('home/badlogin.html', context)


@login_required(login_url='/login')
def view_debug(request):
    """ return the django debug info page. """
    context = {
        'request': request,
        'djangoversion': get_django_version(),
        'sysversion': getattr(settings, 'SYSVERSION', ''),
        'siteversion': getattr(settings, 'SITE_VERSION', ''),
        'siteversionnum': getattr(settings, 'WPVERSION', ''),
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
    if serror not in ('403', '404', '500'):
        serror = '404'
    context = {
        'request': request,
        'request_path': mark_for_escaping(request_path),
    }
    return responses.clean_response_req('home/{}.html'.format(serror),
                                        context,
                                        request=request)


@never_cache
def view_ip(request):
    """  returns the remote ip page. """
    context = {
        'request': request,
    }
    return responses.clean_response('home/ip.html', context)


@never_cache
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

    # log.debug("username: " + str(username) + ", pw: " + str(pw))

    response = responses.redirect_response("/badlogin.html")
    if (username is not None) and (pw is not None):

        user = auth.authenticate(user=username, password=pw)

        # log.debug("USER=" + str(user))

        if user is not None:
            if user.is_active():
                auth.login(request, user)
                referer_view = responses.get_referer_view(request,
                                                          default=None)

                # log.debug("referer_view: " + str(referer_view))

                # Change response based on whether or not prev. view was given.
                if referer_view is None:
                    # Success
                    response = responses.redirect_response('/')
                else:
                    # Previous view
                    response = responses.redirect_response(referer_view)

    return response


def view_no_javascript(request):
    """ Return a page for bots trying to visit base64 or other links that
        are supposed to be decoded with javascript.
    """
    return responses.basic_response(
        'Sorry, you must have javascript enabled to follow that link.'
    )


def view_scriptkids(request):
    """ return my script kiddie view
        for people trying to access wordpress-login pages and stuff like that.
    """

    # get ip if possible.
    # ip_address = request.META.get("HTTP_X_FORWARDED_FOR", None)
    # if ip_address is None:
    #    ip_address = request.META.get("REMOTE_ADDR", None)
    ip_address = utilities.get_remote_ip(request)
    use_ip = (ip_address is not None)
    try:
        path = request.path
    except AttributeError:
        path = '<error getting path>'
    log.error('ScriptKid Access from: {} -> {}'.format(ip_address, path))

    # get insulting image to display
    scriptkid_img = hometools.get_scriptkid_image()
    if scriptkid_img is not None:
        scriptkid_img = utilities.get_relative_path(scriptkid_img)
    use_img = (scriptkid_img is not None)

    context = {
        'request': request,
        'use_img': use_img,
        'scriptkid_img': scriptkid_img,
        'use_ip': use_ip,
        'ip_address': ip_address,
    }
    # return formatted template.
    return responses.clean_response('home/scriptkids.html', context)


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


@never_cache
def view_useragent(request):
    """  returns the user agent page. """
    context = {
        'request': request,
    }
    return responses.clean_response('home/useragent.html', context)


@never_cache
def view_useragent_simple(request):
    """ returns the user agent string in plain text. """
    ua = utilities.get_user_agent(request)
    uastr = getattr(ua, 'ua_string', 'Unknown')
    return responses.text_response('{}\n'.format(uastr))
