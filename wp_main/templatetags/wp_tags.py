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
from wp_main.utilities import htmltools
from wp_main.utilities import utilities
from viewer.highlighter import wp_highlighter
from django.utils.safestring import mark_safe
register = template.Library()


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
    
    server_name = request_object.META['SERVER_NAME']
    return (server_name.startswith('test.') or
            server_name == '127.0.0.1')


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


# tuple of filters to register.
registered_filters = (comments_button,
                      is_false,
                      is_true,
                      exceeds_max,
                      exceeds_min,
                      dict_value,
                      meta_value,
                      is_mobile,
                      is_test_site,
                      contains,
                      starts,
                      ends,
                      highlight_python)

# register all filters in the registered tuple.
for filter_ in registered_filters:
    register.filter(filter_.func_name, filter_)

