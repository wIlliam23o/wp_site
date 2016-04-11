# -*- coding: utf-8 -*-

'''Welborn Productions - Utilities - Responses
    Provides easy access to HttpResponse/Request objects/functions,
    and some helper functions.

    -Christopher Welborn <cj@welbornprod.com> - Mar 27, 2013
'''
import logging

# Default dict for request args.
from collections import defaultdict

# Local tools
from wp_main.utilities import htmltools
from wp_main.utilities.utilities import (
    get_server,
    get_remote_ip,
    logtraceback
)

# Template loading, and Contexts
from django.contrib import messages
from django.http import (
    HttpResponse,
    HttpResponseServerError,
    Http404,
    QueryDict
)
from django.template import RequestContext, Context, loader  # noqa
# Mark Html generated by these functions as safe to view.
from django.utils.safestring import mark_safe

# For the staff_required decorator
from functools import wraps

# JSON stuff
import json

# regex (for get referrer view)
import re

log = logging.getLogger('wp.utilities.responses')


def alert_message(request, alert_msg, **kwargs):
    """ Builds an alert message, and returns the HttpResponse object.
        Arguments:
            request       : The original request
            alert_msg     : What to show in the alert box.

        Keyword Arguments:
            body_message  : Body content wrapped in a wp-block div.
                            Default is "Click here to go home."
            status        : Status code for HTTP. Default: 200
    """

    body_message = kwargs.get(
        'body_message',
        '<a href=\'/\'><span>Click here to go home</span></a>'
    )
    noblock = kwargs.get('noblock', False)

    # passes the body message to the generic 'main_content'
    # block of the main template
    main_content = '<div class=\'wp-block\'>{}</div>'.format(body_message)

    # alert_message will display at the top of the page,
    # per the main templates 'alert_message' block.
    context = {
        'main_content': mark_safe(main_content),
        'alert_message': mark_safe(alert_msg),
    }
    return clean_response(
        'home/main.html',
        context=context,
        request=request,
        status=kwargs.get('status', 200))


def basic_response(scontent='', *args, **kwargs):
    """ just a wrapper for the basic HttpResponse object. """
    return HttpResponse(scontent, *args, **kwargs)


def clamp_num(i, min_val=None, max_val=None):
    """ Ensure a number is between min and max. Alter if needed. """
    if (min_val is not None) and (i < min_val):
        return min_val
    if (max_val is not None) and (i > max_val):
        return max_val
    return i


def clean_response(
        template_name, context=None, request=None, status=200, **kwargs):
    """ same as render_response, except does code cleanup (no comments, etc.)
        returns cleaned HttpResponse.
        Arguments:
            template_name   : Known template name to render.
            context         : Context dict or Context()/RequestContext().
            request         : Request() object (or None).
            status          : Status code for the HttpResponse().

        Keyword Args:
            link_list       : Auto link list for render_html()
            auto_link_args  : Keyword arguments dict for render_html() and
                              auto_link()
    """
    context = context or {}
    # Check kwargs for a request obj, then check the context if it's not
    # there.
    request = request or context.get('request', None)

    # Add request to context if available.
    if request:
        # Add server name, remote ip to context if not added already.
        if not context.get('server_name', False):
            context['server_name'] = get_server(request)
        if not context.get('remote_ip', False):
            context['remote_ip'] = get_remote_ip(request)

    try:
        rendered = htmltools.render_clean(
            template_name,
            context=context,
            request=request,
            link_list=kwargs.get('link_list', None),
            auto_link_args=kwargs.get('auto_link_args', None)
        )
    except Exception:
        logtraceback(log.error, message='Unable to render.')
        # 500 page.
        return error500(request, msgs=('Error while building that page.',))

    if rendered:
        # Return final page response.
        return HttpResponse(rendered, status=status or 200)

    # Something went wrong in the render chain.
    # It catches most errors, logs them, and returns ''.
    msgs = [
        'Unable to build that page right now, sorry.',
        'The error has been logged and emailed to me.'
    ]
    return error500(request, msgs=msgs)


def convert_arg_type(s, default=None, min_val=None, max_val=None):
    """ Convert a request argument (get/post) to it's required type.
        If no default is given, int and float will be tried in that order.
        If those conversions fail, the original value will be returned.
        If converting to default's type fails,  the default value will be
        returned (None when not set).
        Examples:
            # Convert to int:
            convert_arg_type('1', default=0) == 1
            convert_arg_type('1') == 1
            # Convert to float:
            convert_arg_type('1', default=1.0) == 1.0
            convert_arg_type('1.0') == 1.0
            # Can't convert to default type, return default:
            convert_arg_type('blah', default=0) == 0
            # Can't convert to int or float, return original:
            convert_arg_type('blah') == 'blah'
            # Value is less than minimum value, return minimum:
            convert_arg_type('-1', min_val=0) == 0

        Arguments:
            s       : String to convert (coming from request args).
            default : Default value when conversion fails, and type to use.
            min_val : Minimum value. Numbers will be clamped if < min_val.
            max_val : Maximum value. Numbers will be clamped if > max_val.
    """

    # Do automatic type conversion if wanted.
    if (default is not None):
        # Convert value to desired type from defaults type.
        desiredtype = type(default)
        try:
            desiredval = desiredtype(s)
            # If an error isn't raised, we converted successfully.
            return desiredval
        except Exception as ex:
            log.error('Unable to determine type from: {}\n{}'.format(
                s,
                ex))
            return default

    # No default type was passed, try int/float.
    # check min/max for int values
    try:
        int_val = int(s)
        return clamp_num(int_val, min_val=min_val, max_val=max_val)
    except (TypeError, ValueError):
        # try float, check min/max if needed.
        try:
            float_val = float(s)
            return clamp_num(float_val, min_val=min_val, max_val=max_val)
        except (TypeError, ValueError):
            # Not an int or a float, no default type was given.
            return s


def error_response(request=None, errnum=500, msgs=None, user_error=None):
    """ Error Response, with optional messages through the messages framework.
        errnum can be 403, 404, or 500,
        (or any other number with a template in /home)

        If msgs is passed, it is sent via the messages framework.
        Arguments:
            request     : Request object from view.
            errnum      : Int, error number (decides which template to use).
            msgs        : Optional error messages for the messages framework.
                          Accepts a list, or a single string.
            user_error  : Friendly msg to show to the user, usually because it
                          was their fault (invalid request/url).
                          Without it, the default 'sorry, this was my fault..'
                          msg is shown.
    """
    if msgs and isinstance(msgs, str):
        msgs = [msgs]

    if not request:
        # This happens when the request isn't passed from the original view.
        return text_response('\n'.join((
            'A developer error occurred.',
            'The Request() object was lost somewhere down the line.',
            'This error has been emailed to me, and I will fix it asap.',
            'Thanks for your patience, -Cj',
            '\nOriginal message:\n{}'.format('\n'.join(msgs)) if msgs else ''
        )))

    if msgs:
        # Send messages using the message framework.
        for m in msgs:
            messages.error(request, m)

    context = {
        'server_name': get_server(request),
        'remote_ip': get_remote_ip(request),
        'user_error': user_error,
    }
    templatefile = 'home/{}.html'.format(errnum)
    try:
        rendered = htmltools.render_clean(
            templatefile,
            context=context,
            request=request)
    except Exception as ex:
        logmsg = 'Unable to render template: {}\n{}'.format(templatefile, ex)
        log.error(logmsg)
        # Send message manually.
        errmsgfmt = '<html><body>\n{}</body></html>'
        # Style each message.
        msgfmt = '<div style="color: darkred;">{}</div>'
        if msgs:
            errmsgs = '\n'.join((msgfmt.format(m) for m in msgs))
            # Build final html page.
            errmsg = errmsgfmt.format(errmsgs)
        else:
            msgerrnum = 'Error: {}'.format(errnum)
            msgerrtxt = 'There was an error while building this page.'
            errmsg = errmsgfmt.format(
                msgfmt.format('<br>'.join((msgerrnum, msgerrtxt))))
        return HttpResponseServerError(errmsg, status=errnum)
    if not rendered:
        rendered = htmltools.fatal_error_page(
            'Unable to build that page, sorry.')
    # Successfully rendered {errnum}.html page.
    return HttpResponse(rendered, status=errnum)


def error403(request, msgs=None, user_error=None):
    """ 403 Response, with optional messages through the messages framework.
        If msgs is passed, it is sent via the messages framework.
        Arguments:
            request     : Request object from view.
            msgs        : Optional error messages for the messages framework.
                          Accepts a list, or a single string.
            user_error  : Friendly msg to show to the user, usually because it
                          was their fault (invalid request/url).
                          Without it, the default 'sorry, this was my fault..'
                          msg is shown.
    """
    return error_response(request, 403, msgs=msgs, user_error=user_error)


def error404(request, msgs=None):
    """ Raise a 404, but pass an optional message through the messages
        framework.
        Arguments:
            request     : Request object from view.
            msgs        : Optional error messages for the messages framework.
                          Accepts a list, or a single string.
    """

    if msgs and isinstance(msgs, str):
        msgs = [msgs]

    if msgs:
        # Send messages using the message framework.
        for m in msgs:
            messages.error(request, m)

        raise Http404(msgs[0])
    else:
        raise Http404()


def error500(request, msgs=None, user_error=None):
    """ Fake-raise a 500 error. I say fake because no exception is
        raised, but the user is directed to the 500-error page.
        If msgs is passed, it is sent via the messages framework.
        Arguments:
            request     : Request object from view.
            msgs        : Optional error messages for the messages framework.
                          Accepts a list, or a single string.
            user_error  : Friendly msg to show to the user, usually because it
                          was their fault (invalid request/url).
                          Without it, the default 'sorry, this was my fault..'
                          msg is shown.
    """
    return error_response(request, 500, msgs=msgs, user_error=user_error)


def get_paged_args(request, total_count):
    """ retrieve request arguments for paginated post/tag lists.
        total count must be given to calculate last page.
        returns dict with arg names as keys, and values.
    """

    # get order_by
    order_by_ = get_request_arg(request, ['order_by', 'order'], default=None)

    # get max_posts
    max_items = get_request_arg(
        request,
        ('max_items', 'max'),
        default=25,
        min_val=1,
        max_itemsval=100)

    # get start_id
    start_id = get_request_arg(
        request,
        ('start_id', 'start'),
        default=0,
        min_val=0,
        max_val=total_count)
    # calculate last page based on max_posts
    last_page = (total_count - max_items) if (total_count > max_items) else 0
    # fix starting id.
    if hasattr(start_id, 'lower'):
        start_id = last_page if start_id.lower() == 'last' else 0
    else:
        if start_id > total_count:
            # If the start_id is larger than the total posts,
            # start on the last page.
            start_id = last_page

    # fix maximum start_id (must be within the bounds)
    if start_id > (total_count - 1):
        start_id = total_count - 1

    # get prev page
    # (if previous page is out of bounds, just show the first page)
    prev_page = start_id - max_items
    if prev_page < 0:
        prev_page = 0
    # get next page (if next page is out of bounds, just show the last page)
    next_page = start_id + max_items
    if next_page > total_count:
        next_page = last_page

    return {
        'start_id': start_id,
        'max_items': max_items,
        'prev_page': prev_page,
        'next_page': next_page,
        'order_by': order_by_
    }


def get_referer_view(request, default=None):
    ''' Return the referer view of the current request
        Example:
            def some_view(request):
                ...
                referer_view = get_referer_view(request)
                return HttpResponseRedirect(referer_view, '/accounts/login/')
    '''

    # if the user typed the url directly in the browser's address bar
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return default

    # remove the protocol and split the url at the slashes
    referer = re.sub('^https?:\/\/', '', referer).split('/')
    if referer[0] != request.META.get('SERVER_NAME'):
        return default

    # add the slash at the relative path's view and finished
    referer = u'/' + u'/'.join(referer[1:])
    return referer


def get_request_arg(request, arg_names, **kwargs):
    """ return argument from request (GET or POST),
        arg_names can be a list of alias names like: ['q', 'query', 'search']
           and this will look for any of those args.
        default value can be set.
        automatically returns int/float values instead of string where needed.
        min/max can be set for integer/float values.

        * This does not handle multiple args. Only the first one is used.
        * If you need multiple args, you will need to handle them manually.

        Arguments:
            request    : request object to get page args from
            arg_names  : argument names to accept for this arg.

        Keyword Arguments:
            default    : default value for argument if it's not found.
                         Default: None
            method     : 'get' or 'post'. If not given, both are used.
                         POST args override GET arguments.
            min_val    : minimum value for int args.
            max_val    : maximum vlaue for int args.
                         Default: 999999

    """
    reqmethod = kwargs.get('method', None)
    if reqmethod is None:
        # Stack post args on get args (like the old REQUEST).
        requestargs = request.GET.copy()
        requestargs.update(request.POST)
    else:
        # Use desired method only.
        requestargs = getattr(request, reqmethod.upper(), QueryDict())

    default = kwargs.get('default', None)
    if not requestargs:
        return default

    min_val = kwargs.get('min_val', 0)
    max_val = kwargs.get('max_val', 999999)
    # blank value to start with. (until we confirm it exists)
    val = ''
    if isinstance(arg_names, (list, tuple)):
        # list of arg aliases was passed, try them all.
        for arg in arg_names:
            val = requestargs.get(arg, None)
            if val:
                break
    else:
        # single arg_name was passed.
        val = requestargs.get(arg_names, None)

    if val:
        return convert_arg_type(
            val,
            default=default,
            min_val=min_val,
            max_val=max_val)

    return default


def get_request_args(request, requesttype=None):
    """ Returns a QueryDict() of all request args.

        Arguments:
            request  : The request object to retrieve args from.

        Keyword Arguments:
            requesttype  : 'post', 'get', or None.
                           If None is given, it retrieves both POST and GET.

    """

    # Get original request args.
    if requesttype:
        # Try using provided request type.
        try:
            reqargs = getattr(request, requesttype.upper())
        except AttributeError as ex:
            log.error('Invalid request arg type!: {}\n{}'.format(
                requesttype,
                ex))
            return QueryDict()
    else:
        # Default request type is REQUEST (both GET and POST)
        # REQUEST is deprecated, but this will simulate it.
        reqargs = request.GET.copy()
        reqargs.update(request.POST)

    return reqargs


def json_get(data, suppress_errors=False):
    """ Retrieves a dict from json data string. """

    originaltype = type(data)
    if isinstance(data, dict):
        return data

    if hasattr(data, 'decode'):
        data = data.decode('utf-8')

    datadict = None
    try:
        datadict = json.loads(data)
    except TypeError as extype:
        log.debug('Wrong type passed in: {}\n{}'.format(originaltype, extype))
    except ValueError as exval:
        # This happens when url-encoded data is sent in, but we try to get
        # json data first. Logging a 65 line file that has been urlencoded
        # sucks.
        # It could be a real error, so instead of ignoring it
        # I am trimming the data to a smaller size, and logging that and the
        # error. This can be disabled completely by passing:
        # suppress_errors=True, if you know beforehand that this might happen.
        if not suppress_errors:
            sampledata = data[:64]
            log.debug((
                'Bad data passed in:  (first {} chars) == {}\n{}'
            ).format(len(sampledata), sampledata, exval))

    return datadict


def json_get_request(request, suppress_errors=False):
    """ retrieve JSON data from a request (uses json_get()). """

    if hasattr(request, 'body'):
        return json_get(request.body, suppress_errors=suppress_errors)
    return None


def json_response(data):
    """ Returns an HttpResponse with application/json
        data can be a json.dumps() or a dict.
        dicts will be transformed with json.dumps()
    """

    if isinstance(data, dict):
        data = json.dumps(data)

    return HttpResponse(data, content_type='application/json')


def json_response_err(ex, logit=False):
    """ Respond with contents of error message using JSON. """
    if logit:
        log.error('Sent JSON error:\n{}'.format(ex))

    if hasattr(ex, '__class__'):
        extyp = str(ex.__class__)
    else:
        extyp = str(type(ex))

    errdata = {
        'status': 'error',
        'message': str(ex),
        'errortype': extyp,
    }
    return json_response(errdata)


def redirect_perm_response(redirect_to):
    """ returns a permanently moved response. """

    return redirect_response(redirect_to, status_code=301)


def redirect_response(redirect_to, status_code=302):
    """ returns redirect response.
        redirects user to redirect_to.
    """

    response = HttpResponse(redirect_to, status=status_code)
    response['Location'] = redirect_to
    return response


def render_response(template_name, context):
    """ same as render_to_response,
        loads template, renders with context,
        returns HttpResponse.
    """
    request = context.get('request', None) if context else None
    try:
        rendered = htmltools.render_clean(template_name, context)
        return HttpResponse(rendered)
    except Exception as ex:
        log.error(
            'Error rendering template \'{}\': {}'.format(template_name, ex))
        return alert_message(request,
                             'Sorry, there was an error loading this page.')


class staff_required(object):  # noqa

    """ Decorator for views. Redirects straight to 403 if the user isn't staff.
        Allows you to pass in messages for the messages-framework.
        Arguments:
            msgs       : List of error messages to pass to the framework.
                         Can be a list/tuple of strings, or just a string.
            user_error : A friendlier error message for the user.
                         (not in bold red like the error messages.)
                         Can be a string, newline-separated string,
                         or list/tuple of strings.

            * Arguments are for error_response().
    """

    def __init__(self, msgs=None, user_error=None):
        self.msgs = msgs
        self.user_error = self.format_error(user_error)

    def __call__(self, func):
        """ Decorator to wrap views.
            If the user is not logged in and staff,
            a 403 page is returned instead of asking them to log in.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not args[0].user.is_staff:
                return error403(
                    args[0],
                    msgs=self.msgs,
                    user_error=self.user_error)
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def format_error(usererr):
        """ Formats a list/str of msgs into basic divs. """
        if not usererr:
            return None
        if isinstance(usererr, (list, tuple)):
            lines = usererr
        else:
            lines = str(usererr).split('\n')
        linefmt = '</div>\n<div>'.join(lines)
        return '\n<div>{}</div>\n'.format(linefmt)


def text_response(text_content, content_type='text/plain'):
    """ sends basic HttpResponse with content type as text/plain """

    return HttpResponse(text_content, content_type=content_type)


def wsgi_error(request, smessage):
    """ print message to requests wsgi errors """

    request.META['wsgi_errors'] = smessage


def xml_response(template_name, context=None):
    """ loads sitemap.xml template, renders with context,
        returns HttpResponse with content_type='application/xml'.
    """
    contextdict = context or {}
    try:
        tmplate = loader.get_template(template_name)
        contextobj = Context(contextdict)
        clean_render = htmltools.remove_whitespace(
            htmltools.remove_comments(tmplate.render(contextobj)))
        response = HttpResponse(clean_render, content_type='application/xml')
    except Exception as ex:
        errmsg = 'Error: {}'.format(ex)
        response = HttpResponseServerError(errmsg, content_type='text/plain')

    return response
