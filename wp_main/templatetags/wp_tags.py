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


def is_mobile(value):
    """ value is the request from the view, 
        this is actually not needed with django_user_agents installed.
        you can just use: request.user_agent.is_mobile
        returns whether or not the client is mobile/tablet.
    """
    
    return utilities.is_mobile(value)


register.filter('comments_button', comments_button)
register.filter("is_false", is_false)
register.filter("is_true", is_true)
register.filter("exceeds_max", exceeds_max)
register.filter("exceeds_min", exceeds_min)
register.filter('is_mobile', is_mobile)