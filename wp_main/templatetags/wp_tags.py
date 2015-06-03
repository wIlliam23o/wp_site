#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welbornproductions - global template tags
     @summary: provides template tags that can be used in any wp app.

      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>

   start date: Mar 29, 2013
'''
# For insert_video, building a mimetype from file extension.
import os

import base64
import logging

# Django stuff
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


# Local tools
from wp_main.utilities import utilities
from wp_main.utilities.highlighter import WpHighlighter, highlight_codes

# for admin site filtering
from blogger.models import wp_blog
from img.models import wp_image
from projects.models import wp_project
from misc.models import wp_misc
from apps.models import wp_app
from apps.phonewords.models import pw_result
from apps.paste.models import wp_paste

log = logging.getLogger('wp.wp_main.tags')

register = template.Library()

# for admin change_list filtering.
import re
#                               adminpage type  id     str()
disabled_patstr = r'<a href.+"/(admin\w+)/(.+)/(\d+)/">(.+)</a>'
disabled_pat = re.compile(disabled_patstr)


@register.filter
def b64decode(s):
    """ Decode a Base64 string. """
    return base64.decodebytes(s.encode('utf-8')).decode('utf-8')


@register.filter
def b64encode(s):
    """ Base64 encode a string. """
    return base64.encodebytes(s.encode('utf-8')).decode('utf-8').strip()


@register.filter
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
                log.error('Failed to parsed disable-item id: '
                          '{}\n{}'.format(idstr, ex))
                return item

            # name/title of object (My Blog Post)
            name = obj_match.groups()[3]
        else:
            # failed to match our pattern exactly.
            log.debug("Incorrect number of items in match: " + str(item))
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
    log.debug('Found: {}'.format(obj))
    # no object found for this type.
    if obj is None:
        log.debug(''.join((
            'Colorize-Admin: Can\'t find: '
            '{} [{}]')).format(name, otype))
        return item

    # List of classes to add to this link.
    newclasses = []

    # Add classes based on object attributes.
    if is_disabled(obj):
        # Item is disabled (could be post, project, misc, paste, etc.)
        newclasses.append('item-disabled')

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
    except:  # Exception as ex:
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
        except:
            val_ = value

    if isinstance(max_, (float, int)):
        return (val_ > max_)
    else:
        if max_.isalnum():
            try:
                imax = int(max_)
                return (val_ > imax)
            except:
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
        except:
            val_ = value
    if isinstance(min_, (float, int)):
        return (val_ < min_)
    else:
        if min_.isalnum():
            try:
                imin = int(min_)
                return (val_ < imin)
            except:
                pass

    return False


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
    """ Shortcut to utilities.get_time_since(date, limit=True). """
    if not date:
        return date
    since = utilities.get_time_since(date, limit=True)
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
    """ checks python value for false """

    return (value is False)


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
def is_true(value):
    """ checks python value for true """

    return (value is True)


@register.filter
def log_debug(data):
    """ writes something to the log. str(data) is used on objects,
        returns original object.
    """

    if hasattr(data, 'encode'):
        s = data
    elif isinstance(data, (list, tuple)):
        s = '\n'.join(data)
    else:
        s = str(data)
    log.debug(s)
    return data


@register.filter
def meta_value(request_object, dictkey):
    """ returns .META dict value from request """

    try:
        val = request_object.META[dictkey]
    except:  # Exception as ex:
        val = ''
    return val


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
def starts(str_, val_to_check):
    """ uses str_.startswith() to check a value.
        returns True if str_.startswith(val_to_check)
    """

    return (str_.startswith(val_to_check))


@register.filter
def str_(object_):
    """ returns str(object_) to the template. """
    return str(object_)


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
