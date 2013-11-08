#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welbornproductions - global template tags
     @summary: provides template tags that can be used in any wp app.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 29, 2013
'''

from django import template
from django.conf import settings
from wp_main.utilities import htmltools
from wp_main.utilities import utilities
from wp_main.utilities.highlighter import wp_highlighter
from wp_main.utilities.wp_logging import logger
# for admin site filtering
from blogger.models import wp_blog
from projects.models import wp_project
from misc.models import wp_misc

_log = logger("wp_tags").log

from django.utils.safestring import mark_safe
register = template.Library()

# for admin change_list filtering.
import re

def comments_button(value):
    """ returns comments button for this blog post. """
    
    return mark_safe(htmltools.comments_button('/blog/view/' + value.slug))


def is_false(value):
    """ checks python value for false """
    
    return (value is False)


def is_true(value):
    """ checks python value for true """
    
    return (value is True)


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


def dict_value(dict_object, dictkey):
    """ retrieves value for dict key,
        like: value['dictkey'].
    """
    
    try:
        val = dict_object[dictkey]
    except: # Exception as ex:
        val = ''
    return val


def meta_value(request_object, dictkey):
    """ returns .META dict value from request """
    
    try:
        val = request_object.META[dictkey]
    except: # Exception as ex:
        val = ''
    return val


def is_mobile(request_object):
    """ determines whether or not the client is mobile/tablet.
        requires a request object.
        returns True/False.
    """
    
    return utilities.is_mobile(request_object)


def is_test_site(request_object):
    """ determines whether or not the site is a test-server.
        looks for 'test.welbornprod' domains.
        returns True/False.
    """
    if request_object is None or request_object.META is None:
        # happens on template errors, which hopefully don't make it to production.
        return True
    # Get current server name for this instance.
    # Could be the live server, test server, or local server 
    # the local server_name changes depending on where it's accessed from.
    server_name = request_object.META['SERVER_NAME']
    
    return (server_name.startswith('test.') or      # remote test site
            (server_name in settings.INTERNAL_IPS)) # local dev


def contains(str_or_list, val_to_find):
    """ uses 'if val in str_or_list'.
        returns True if val_to_find is in str_or_list.
    """
    
    return (val_to_find in str_or_list)


def starts(str_, val_to_check):
    """ uses str_.startswith() to check a value.
        returns True if str_.startswith(val_to_check)
    """
    
    return (str_.startswith(val_to_check))


def ends(str_, val_to_check):
    """ uses str_.endswith() to check a value.
        returns True if str_.endswith(val_to_check)
    """
    
    return (str_.endswith(val_to_check))


def highlight_python(scontent):
    """ highlight code using lexer by name.
        line numbers are optional.
        This is really for the debug page.
    """
    
    try:
        highlighter = wp_highlighter(lexer_name_='python', line_nums_=False)
        highlighter.code = scontent
        results = highlighter.highlight()
    except:
        results = scontent
    return results


def debug_allowed(request_object):
    """ uses utilities to determine if debug info is allowed for this request. """
    
    return utilities.debug_allowed(request_object)


def is_disabled(model_obj):
    """ if object has .disabled attribute, returns it,
        if not, returns False.
    """
    
    if hasattr(model_obj, 'disabled'):
        return model_obj.disabled
    else:
        return False

def log_debug(data):
    """ writes something to the log. str(data) is used on objects,
        returns original object.
    """
    
    if isinstance(data, (str, unicode)):
        s = data
    elif isinstance(data, (list, tuple)):
        s = '\n'.join(data)
    else:
        s = str(data)
    _log.debug(s)
    return data

def str_(object_):
    """ returns str(object_) to the template. """
    return str(object_)


def get_remote_host(request):
    """ Same as get_remote_ip, except for hostname. """
    
    return utilities.get_remote_host(request)


def get_remote_ip(request):
    """ Make the convenience function available for templates. """
    
    return utilities.get_remote_ip(request)

   
def repr_(object_):
    """ returns repr(object_) to the template """
    return repr(object_)


def disabled_css(item):
    """ applies class='item-disabled' to admin change_list.results.item
        if the object has .disabled attribute and it is set to True.
        This is used in change_list_results.html template for admin.
    """
    #                           tag         adminpage   object  name/title
    obj_pattern = re.compile(r'(<a href).+("/admin\w+)/(.+)/">([\(\)\!\-\w\d\. ]+)</a>')
    obj_match = obj_pattern.search(item)
    if obj_match is None:
        return item
    else:
        # grab object.
        if len(obj_match.groups()) == 4:
            # beginning of a tag (<a href)
            tag = obj_match.groups()[0] #@UnusedVariable: tag
            # type of object (wp_blog/1)
            otype = obj_match.groups()[2].strip('/')
            # name/title of object (My Blog Post)
            name = obj_match.groups()[3]
        else:
            # failed to match our pattern exactly.
            _log.debug("Incorrect number of items in match: " + str(item))
            return item
    # tag, type, & name should be set now, parse them
    if name.startswith('(!)'): name = name[3:]
    if 'v. ' in name: name = name[:name.index('v. ')]
    name = name.strip(' ')
    # parse type
    if '/' in otype: otype = otype[:otype.index('/')]
    
    # convert to object
    if 'wp_blog' in otype:
        obj = utilities.get_object_safe(wp_blog.objects, title=name)
    elif 'wp_project' in otype:
        obj = utilities.get_object_safe(wp_project.objects, name=name)
    elif 'wp_misc' in otype:
        obj = utilities.get_object_safe(wp_misc.objects, name=name)
    else:
        _log.debug("Object type not filtered yet: " + otype)
        obj = None
    # no object found
    if obj is None:
        _log.debug("No object found for: " + name + " [" + otype + "]")
        return item
    
    # item is disabled?
    if is_disabled(obj):
        return mark_safe(item.replace('<a href', '<a class="item-disabled" href'))
    else:
        # item was not disabled.
        return item
    

def get_filename(filename):
    """ uses utilities and os.path to return only the short filename (no path) """
    
    return utilities.get_filename(filename)


# tuple of filters to register.
registered_filters = (comments_button,
                      is_false,
                      is_true,
                      exceeds_max,
                      exceeds_min,
                      dict_value,
                      get_remote_host,
                      get_remote_ip,
                      meta_value,
                      is_mobile,
                      is_test_site,
                      contains,
                      starts,
                      ends,
                      highlight_python,
                      debug_allowed,
                      is_disabled,
                      log_debug,
                      str_,
                      repr_,
                      disabled_css,
                      get_filename)

# register all filters in the registered tuple.
for filter_ in registered_filters:
    register.filter(filter_.func_name, filter_)

