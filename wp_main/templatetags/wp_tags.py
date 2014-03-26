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

# Django stuff
from django import template
from django.conf import settings
# Local tools
from wp_main.utilities import htmltools
from wp_main.utilities import utilities
from wp_main.utilities.highlighter import wp_highlighter
from wp_main.utilities.wp_logging import logger
# for admin site filtering
from blogger.models import wp_blog
from projects.models import wp_project
from misc.models import wp_misc
from apps.models import wp_app
from apps.phonewords.models import pw_result
from apps.paste.models import wp_paste

_log = logger("wp_main.tags").log

from django.utils.safestring import mark_safe
register = template.Library()

# for admin change_list filtering.
import re
#                               adminpage type  id     str()
disabled_patstr = r'<a href.+"/(admin\w+)/(.+)/(\d+)/">(.+)</a>'
#disabled_patstr = r'(<a href).+"/(admin\w+)/(.+)/(\d+)/">(.+)</a>'
#disabled_patstr = r'(<a href).+"/(admin\w+)/(.+)/">(.+)</a>'
disabled_pat = re.compile(disabled_patstr)


def comments_button(value):
    """ returns comments button for this blog post. """
    # TODO: Put this is blogger_tags where it belongs..!
    return mark_safe(htmltools.comments_button('/blog/view/' + value.slug))


def contains(str_or_list, val_to_find):
    """ uses 'if val in str_or_list'.
        returns True if val_to_find is in str_or_list.
    """
    
    return (val_to_find in str_or_list)


def debug_allowed(request_object):
    """ uses utilities to determine if debug 
        info is allowed for this request.
    """
    
    return utilities.debug_allowed(request_object)


def dict_value(dict_object, dictkey):
    """ retrieves value for dict key,
        like: value['dictkey'].
    """
    
    try:
        val = dict_object[dictkey]
    except:  # Exception as ex:
        val = ''
    return val


def disabled_css(item):
    """ applies class='item-disabled' to admin change_list.results.item
        if the object has .disabled attribute and it is set to True.
        This is used in change_list_results.html template for admin.
    """
 
    obj_match = disabled_pat.search(item)
    if obj_match is None:
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
                _log.error('Failed to parsed disable-item id: '
                           '{}\n{}'.format(idstr, ex))
                return item

            # name/title of object (My Blog Post)
            name = obj_match.groups()[3]
        else:
            # failed to match our pattern exactly.
            _log.debug("Incorrect number of items in match: " + str(item))
            return item
    
    # convert to object
    objectsets = {
        'wp_app': wp_app.objects,
        'wp_blog': wp_blog.objects,
        'wp_project': wp_project.objects,
        'wp_misc': wp_misc.objects,
        'wp_paste': wp_paste.objects,
        'pw_result': pw_result.objects,
    }
    obj = None
    for objname, objects in objectsets.items():
        if objname == otype:
            obj = utilities.get_object_safe(objects, id=objid)
            break

    # no object found for this type.
    if obj is None:
        _log.debug('Admin-disable: Can\'t find: '
                   '{} [{}]'.format(name, otype))
        return item
    
    # item is disabled?
    if is_disabled(obj):
        return mark_safe(item.replace('<a href',
                                      '<a class="item-disabled" href'))
    else:
        # item was not disabled.
        return item
    

def ends(str_, val_to_check):
    """ uses str_.endswith() to check a value.
        returns True if str_.endswith(val_to_check)
    """
    
    return (str_.endswith(val_to_check))


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


def getlength(lennable):
    """ Tag for len() """

    return len(lennable)


def get_filename(filename):
    """ uses utilities and os.path to return only
        the short filename (no path)
    """
    
    return utilities.get_filename(filename)


def get_remote_host(request):
    """ Same as get_remote_ip, except for hostname. """
    
    return utilities.get_remote_host(request)


def get_remote_ip(request):
    """ Make the convenience function available for templates. """
    
    return utilities.get_remote_ip(request)


def highlight_python(scontent):
    """ highlight code using lexer by name.
        line numbers are optional.
        This is really for the debug page.
    """
    
    try:
        highlighter = wp_highlighter(lexer_name='python', line_nums=False)
        highlighter.code = scontent
        results = highlighter.highlight()
    except Exception as ex:
        _log.error('Error in highlight_python:\n{}'.format(ex))
        results = scontent
    return results


def insert_video(videourl, posterimg=None, id_=None):
    """ Return a Video.js video player with a url to a video.
        video.css and video.js must be included in <head>!
        ****************************************************************
        ** This has not been tested, and won't be until
        ** the project, blog, etc. pages use template-rendering to load.
        ** see: htmltools.load_html_file()
        ****************************************************************
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


def is_disabled(model_obj):
    """ if object has .disabled attribute, returns it,
        if not, returns False.
    """
    
    if hasattr(model_obj, 'disabled'):
        return model_obj.disabled
    else:
        return False


def is_false(value):
    """ checks python value for false """
    
    return (value is False)


def is_mobile(request_object):
    """ determines whether or not the client is mobile/tablet.
        requires a request object.
        returns True/False.
    """
    
    return utilities.is_mobile(request_object)


def is_none(obj):
    """ Return whether a value is actually None (not falsey) """
    return obj is None


def is_staff(request):
    """ Returns true if the user is an admin. """

    if request:
        if hasattr(request, 'user') and request.user.is_authenticated():
            return request.user.is_staff
    return False


def is_test_site(request_object):
    """ determines whether or not the site is a test-server.
        looks for 'test.welbornprod' domains.
        returns True/False.
    """
    if (request_object is None or
       request_object.META is None or
       (not request_object)):
        # happens on errors,
        # Should always do what the live site does in case of error.
        return False

    # Get current server name for this instance.
    # Could be the live server, test server, or local server
    # the local server_name changes depending on where it's accessed from.
    server_name = request_object.META['SERVER_NAME']
    
    return (server_name.startswith('test.') or      # remote test site
            (server_name in settings.INTERNAL_IPS))  # local dev


def is_true(value):
    """ checks python value for true """
    
    return (value is True)


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
    _log.debug(s)
    return data


def meta_value(request_object, dictkey):
    """ returns .META dict value from request """
    
    try:
        val = request_object.META[dictkey]
    except:  # Exception as ex:
        val = ''
    return val


def repr_(object_):
    """ returns repr(object_) to the template """
    return repr(object_)


def sortdict(d):
    """ Generator for returning an iterable of a sorted dict.
        Can be retrieved like:
            for skey, sval in sortdict(mydict):
        Or in a template:
            {% for skey, sval in mydict|sortdict %}
    """

    for skey in sorted(d.keys()):
        yield (skey, d[skey])


def sortitems(o):
    """ wrapper for sorted() """

    return sorted(o)


def starts(str_, val_to_check):
    """ uses str_.startswith() to check a value.
        returns True if str_.startswith(val_to_check)
    """
    
    return (str_.startswith(val_to_check))


def str_(object_):
    """ returns str(object_) to the template. """
    return str(object_)


def subtract(val, otherval=None):
    """ Do subtraction in a template. """
    if otherval is None:
        return val

    try:
        answer = val - int(otherval)
        return answer
    except ValueError:
        return val


# tuple of filters to register.
registered_filters = (
    comments_button,
    contains,
    debug_allowed,
    dict_value,
    disabled_css,
    ends,
    exceeds_max,
    exceeds_min,
    getlength,
    get_filename,
    get_remote_host,
    get_remote_ip,
    highlight_python,
    insert_video,
    is_disabled,
    is_false,
    is_mobile,
    is_none,
    is_staff,
    is_test_site,
    is_true,
    log_debug,
    meta_value,
    repr_,
    sortdict,
    sortitems,
    starts,
    str_,
    subtract,
    utilities.get_date,
    utilities.get_datetime,
    utilities.get_time,
    utilities.get_time_since,
)

# register all filters in the registered tuple.
for filter_ in registered_filters:
    register.filter(filter_.__name__, filter_)
