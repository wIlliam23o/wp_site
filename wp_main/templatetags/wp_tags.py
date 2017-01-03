#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welbornproductions - global template tags
     @summary: provides template tags that can be used in any wp app.

      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>

   start date: Mar 29, 2013
'''
import os
import base64
import logging
from collections import Iterable

# Django stuff
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


# Local tools
from wp_main.utilities import utilities
from wp_main.utilities.responses import get_request_arg
from wp_main.utilities.highlighter import WpHighlighter, highlight_codes

# for admin site filtering
from blogger.models import wp_blog
from img.models import wp_image
from projects.models import wp_project
from misc.models import wp_misc
from apps.models import wp_app
from apps.phonewords.models import pw_result
from apps.paste.models import wp_paste


# for admin change_list filtering.
import re
# Example of a 'result' item being passed to colorize_admin_css():
# <th class="field-__str__"><a href="/adminmisc/wp_misc/7/change/">XTools v. 0.3.6</a></th>  # noqa
#                               adminpage type  id     str()
disabled_patstr = r'<a href.+"/(admin\w+)/(.+)/(\d+)/[\w]+/">(.+)</a>'
disabled_pat = re.compile(disabled_patstr)

log = logging.getLogger('wp.wp_main.tags')

register = template.Library()


@register.filter
def b64decode(s):
    """ Decode a Base64 string. """
    return base64.decodebytes(s.encode('utf-8')).decode('utf-8')


@register.filter
def b64encode(s):
    """ Base64 encode a string. """
    return base64.encodebytes(s.encode('utf-8')).decode('utf-8').strip()


@register.filter  # noqa
def colorize_admin_css(item):
    """ applies class='item-disabled' to admin change_list.results.item
        if the object has .disabled attribute and it is set to True.
        This is used in change_list_results.html template for admin.
    """
    obj_match = disabled_pat.search(item)
    if obj_match is None:
        log.debug('Not an object link: {}'.format(item))
        # This is not an object link.
        return item
    else:
        log.debug('Found object link: {}'.format(item))
        # grab object.
        if len(obj_match.groups()) == 4:
            # beginning of a tag (<a href) (Not used right now)
            # tag = obj_match.groups()[0]  # noqa
            # type of object (wp_blog)
            otype = obj_match.groups()[1].strip('/')
            idstr = obj_match.groups()[2]
            try:
                objid = int(idstr)
            except Exception as ex:
                log.error(
                    'Failed to parsed disable-item id: {}\n{}'.format(
                        idstr,
                        ex
                    )
                )
                return item

            # name/title of object (My Blog Post)
            name = obj_match.groups()[3]
        else:
            # failed to match our pattern exactly.
            log.debug('Incorrect number of items in match: {}'.format(item))
            return item

    # convert to object
    objectsets = {
        'wp_app': wp_app.objects,
        'wp_blog': wp_blog.objects,
        'wp_project': wp_project.objects,
        'wp_misc': wp_misc.objects,
        'wp_paste': wp_paste.objects,
        'pw_result': pw_result.objects,
        'wp_image': wp_image.objects,
    }
    obj = None
    for objname, objects in objectsets.items():
        if objname == otype:
            obj = utilities.get_object_safe(objects, id=objid)
            break
    log.debug('Found object from result item: {}'.format(obj))
    # no object found for this type.
    if obj is None:
        log.error(
            'Colorize-Admin: Can\'t find: {} [{}]'.format(name, otype)
        )
        return item

    # List of classes to add to this link.
    # The starting class is to add specificity to the css.
    newclasses = ['.wp-admin']

    # Add classes based on object attributes.
    if is_disabled(obj):
        # Item is disabled (could be post, project, misc, paste, etc.)
        newclasses.append('item-disabled')

    # Paste-specific colors.
    # TODO: Like searchables and updateables, make colorize_admin an app-based
    #       check. Have a admin_colors.py that defines a colorizable result.
    if is_onhold(obj):
        # Item is onhold.
        newclasses.append('item-onhold')

    if is_private(obj):
        # Item is a private paste.
        newclasses.append('item-private')

    if is_expired(obj):
        # Item is an expired paste.
        newclasses.append('item-expired')

    if newclasses:
        # Return item with new classes added.
        newtxt = '<a class="{}" href'.format(' '.join(newclasses))
        # Only replace the link part, because it may be wrapped with something
        return mark_safe(item.replace('<a href', newtxt))
    else:
        return item


@register.filter
def contains(str_or_list, val_to_find):
    """ uses 'if val in str_or_list'.
        returns True if val_to_find is in str_or_list.
    """

    return (val_to_find in str_or_list)


@register.filter
def debug_allowed(request_object):
    """ uses utilities to determine if debug
        info is allowed for this request.
    """

    return utilities.debug_allowed(request_object)


@register.filter
def dict_value(dict_object, dictkey):
    """ retrieves value for dict key,
        like: value['dictkey'].
    """

    try:
        val = dict_object[dictkey]
    except (AttributeError, KeyError):
        val = ''
    return val


@register.filter
def ends(str_, val_to_check):
    """ uses str_.endswith() to check a value.
        returns True if str_.endswith(val_to_check)
    """

    return (str_.endswith(val_to_check))


@register.filter
def exceeds_max(value, max_):
    """ checks if a value exceeds the maximum allowed """

    if isinstance(value, (float, int)):
        val_ = value
    else:
        try:
            val_ = int(value)
        except (TypeError, ValueError):
            val_ = value

    if isinstance(max_, (float, int)):
        return (val_ > max_)
    else:
        if max_.isalnum():
            try:
                imax = int(max_)
                return (val_ > imax)
            except (TypeError, ValueError):
                pass
    return False


@register.filter
def exceeds_min(value, min_):
    """ checks if a value exceeds the minimum allowed """

    if isinstance(value, (float, int)):
        val_ = value
    else:
        try:
            val_ = int(value)
        except (TypeError, ValueError):
            val_ = value
    if isinstance(min_, (float, int)):
        return (val_ < min_)
    else:
        if min_.isalnum():
            try:
                imin = int(min_)
                return (val_ < imin)
            except (TypeError, ValueError):
                pass

    return False


@register.filter
def feature(request, featurename):
    """ Check for feature enabled by request arg.
        These features are available to all users!
    """
    return utilities.parse_bool(
        get_request_arg(request, featurename, default='')
    )


@register.filter
def get_browser_style(request):
    """ Get specific browser style based on the user agent. """
    try:
        cssfile = utilities.get_browser_style(request)
    except Exception as ex:
        # Not a valid request object.
        log.error(
            'Unable to get browser style with: {!r}\n  {}'.format(request, ex)
        )
        return None
    return cssfile


@register.filter
def get_length(lennable):
    """ Tag for len() """
    if not lennable:
        return 0

    try:
        return len(lennable)
    except TypeError:
        # Non len()able type.
        return 0


@register.filter
def get_filename(filename):
    """ uses utilities and os.path to return only
        the short filename (no path)
    """

    return utilities.get_filename(filename)


@register.filter
def get_remote_host(request):
    """ Same as get_remote_ip, except for hostname. """

    return utilities.get_remote_host(request)


@register.filter
def get_remote_ip(request):
    """ Make the convenience function available for templates. """

    return utilities.get_remote_ip(request)


@register.filter
def get_time_since(date):
    """ Shortcut to utilities.get_time_since(date, limit=7). """
    if not date:
        return date
    since = utilities.get_time_since(date, limit=7)
    return since if ':' in since else '{} ago'.format(since)


@register.filter
def get_user_agent(request):
    """ Get the user agent string from a request. """
    return utilities.get_user_agent(request)


@register.filter
def hcodes(content):
    """ Highlight using short codes found with highlighter.highlight_codes.
        Example:
        {{ "[py]import os[?py]"|hcodes }}
    """
    if not content:
        return content
    return mark_safe(highlight_codes(content))


@register.filter
def highlight_python(scontent):
    """ highlight code using lexer by name.
        line numbers are optional.
        This is really for the debug page.
    """

    try:
        highlighter = WpHighlighter(lexer_name='python', line_nums=False)
        highlighter.code = scontent
        results = highlighter.highlight()
    except Exception as ex:
        log.error('Error in highlight_python:\n{}'.format(ex))
        results = scontent
    return results


@register.filter
def insert_video(videourl, posterimg=None, id_=None):
    """ Return a Video.js video player with a url to a video.

        video.css and video.js must be included in < head >!
        This has not been tested, and won't be until
        the project, blog, etc. pages use template-rendering to load.
        see: htmltools.load_html_file()
    """
    # TODO: This is not used anywhere, and probably shouldn't be.
    # TODO: Use a Node instead of a Filter, test with PyVal page.
    if not videourl:
        return ''
    # Build arg dict for basehtml.format()
    formatargs = {'videourl': videourl}

    # Grab mimetype.
    fileext = os.path.splitext(videourl)[-1]
    # Should be 'video/{file extension without .}' (works for mp4 and webm)
    formatargs['mimetype'] = 'video/{}'.format(fileext.strip('.'))

    if posterimg:
        # Build poster tag.
        formatargs['postertag'] = 'poster="{}" '.format(posterimg)
    else:
        formatargs['postertag'] = ''

    # Use custom tag id if wanted.
    if id_:
        formatargs['videoid'] = id_
    else:
        formatargs['videoid'] = 'videoplayer'

    # Base template for all videos.
    basehtml = ('\n<video id="{videoid}" class="video-js vjs-default-skin" '
                'controls preload="auto" width="640" height="264" '
                '{postertag}data-setup="{{}}">'
                '\n<source src="{videourl}" type=\'{mimetype}\'>'
                '\n</video>\n')
    # Format basehtml and return it.
    return basehtml.format(**formatargs)


@register.filter
def is_authenticated(req_or_user):
    """ Shortcut to request.user.is_authenticated() """
    if not req_or_user:
        errmsgfmt = 'Falsey object passed to is_authenticated(): {!r}'
        log.error(errmsgfmt.format(req_or_user))
        return False

    if hasattr(req_or_user, 'user'):
        user = getattr(req_or_user, 'user')
    else:
        user = req_or_user

    if hasattr(user, 'is_authenticated'):
        try:
            isauthed = user.is_authenticated()
            return isauthed
        except Exception as exauthcall:
            errmsgfmt = 'Can\'t call is_authenticated() on: {}\n{}'
            log.error(errmsgfmt.format(user, exauthcall))
            return False
    # Request or User was not passed!
    log.error('is_authenticated(): No \'user\' or \'is_authenticated\' attr!')
    return False


@register.filter
def is_disabled(model_obj):
    """ if object has .disabled attribute, returns it,
        if not, returns False.
    """
    return getattr(model_obj, 'disabled', False)


@register.filter
def is_expired(paste_obj):
    """ if object has .is_expired() function, returns the result.
        if not, returns False.
    """

    if hasattr(paste_obj, 'is_expired'):
        try:
            expired = paste_obj.is_expired()
        except TypeError:
            expired = False
    else:
        expired = False
    return expired


@register.filter
def is_false(value):
    """ Whether a value is False, not just falsey. """

    return (value is False)


@register.filter
def is_localdev(request):
    """ Return True if the site is running locally. """
    return settings.SERVER_LOCATION.lower() == 'local'


@register.filter
def is_mobile(request_object):
    """ determines whether or not the client is mobile/tablet.
        requires a request object.
        returns True/False.
    """

    return utilities.is_mobile(request_object)


@register.filter
def is_none(obj):
    """ Return whether a value is actually None (not falsey) """
    return obj is None


@register.filter
def is_onhold(model_obj):
    """ if object has .disabled attribute, returns it,
        if not, returns False.
    """
    return getattr(model_obj, 'onhold', False)


@register.filter
def is_private(obj):
    """ If object has a .private attribute, returns it.
        if not, returns False.
    """
    return getattr(obj, 'private', False)


@register.filter
def is_staff(request):
    """ Returns true if the user is an admin. """

    if request:
        if hasattr(request, 'user') and request.user.is_authenticated():
            return request.user.is_staff
    return False


@register.filter
def is_test_site(request):
    """ determines whether or not the site is a test-server.
        looks for 'test.welbornprod' domains.
        returns True/False.
    """
    if (not request) or (not getattr(request, 'META', None)):
        # happens on errors,
        # Should always do what the live site does in case of error.
        return False

    # Get current server name for this instance.
    # Could be the live server, test server, or local server
    # the local server_name changes depending on where it's accessed from.
    server_name = request.META.get('SERVER_NAME', '')

    return (
        server_name.startswith('test.') or       # remote test site
        (server_name in settings.INTERNAL_IPS))  # local dev


@register.filter
def is_textmode(request):
    """ Return True if the User Agent is from a known text mode browser. """
    return utilities.is_textmode(request)


@register.filter
def is_true(value):
    """ Whether a value is actually True, not just truthy. """

    return (value is True)


@register.filter
def is_viewable(request):
    """ Returns True for the production site and local development.
        Returns False if:
            This is a test site and the user is not authenticated.
    """
    if is_localdev(request):
        # Local dev is always allowed.
        return True
    if is_test_site(request):
        # Staff only for test site.
        return is_staff(request)
    # Production requires no login.
    return True


@register.filter
def log_debug(data):
    """ Writes something to the debug log. str(data) is used on objects,
        returns an empty string.
    """
    log.debug(log_safe(data))
    return ''


@register.filter
def log_error(data):
    """ Writes something to the error log. str(data) is used on objects,
        returns and empty string.
    """
    log.error(log_safe(data))
    return ''


def log_safe(data):
    """ Ensure an object is stringified for log output.
        Lists/Tuples are separated by a newline.
    """
    if isinstance(data, str):
        return data.lstrip()
    elif isinstance(data, bytes):
        try:
            s = data.decode()
        except UnicodeDecodeError:
            s = repr(data)
            log.error('Invalid unicode passed in: {}'.format(s))
        return s
    elif isinstance(data, Iterable):
        return '\n'.join(str(x) for x in data)

    log.error('Unsupported type passed: {}\n  {}'.format(
        type(data).__name__,
        data
    ))
    return str(data).lstrip()


@register.filter
def meta_value(request_object, dictkey):
    """ returns .META dict value from request """

    try:
        val = request_object.META[dictkey]
    except (AttributeError, KeyError):
        val = ''
    return val


@register.filter
def replace(s, replacestr, replacement):
    """ Replace occurrences of `replacestr` with `replacement`. """
    return str(s).replace(str(replacestr), str(replacement))


@register.filter
def repr_(object_):
    """ returns repr(object_) to the template """
    return repr(object_)


@register.filter
def sortdict(d):
    """ Generator for returning an iterable of a sorted dict.
        Can be retrieved like:
            for skey, sval in sortdict(mydict):
        Or in a template:
            {% for skey, sval in mydict|sortdict %}
    """

    for skey in sorted(d.keys()):
        yield (skey, d[skey])


@register.filter
def sortitems(o):
    """ wrapper for sorted() """

    return sorted(o)


@register.filter
def starts(s, val_to_check):
    """ uses str.startswith() to check a value.
        returns True if s.startswith(val_to_check)
    """

    return s.startswith(val_to_check)


@register.filter
def subtract(val, otherval=None):
    """ Do subtraction in a template. """
    if otherval is None:
        return val

    try:
        answer = val - int(otherval)
        return answer
    except ValueError:
        return val


# tuple of basic (no arg) functions/filters to register from other modules.
registered_filters = (
    mark_safe,
    utilities.get_date,
    utilities.get_datetime,
    utilities.get_time,
)

# register all filters in the registered tuple.
for filter_ in registered_filters:
    register.filter(filter_.__name__, filter_)
