#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
          project: utilities.py
         @summary: various tools/utilities for the welbornproductions.net django site..
    
          @author: Christopher Welborn <cj@welbornproductions.net>
    @organization: welborn productions <welbornproductions.net>
"""

import os.path
from os import walk #@UnusedImport: walk is used, pydev...really?
# global settings
from django.conf import settings
# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport

# use log wrapper for debug and file logging.
from wp_main.utilities.wp_logging import logger
_log = logger("utilities").log


def slice_list(list_, starting_index=0, max_items=-1):
    """ slice a list starting at: starting index.
        if max_items > 0 then only that length of items is returned.
        otherwise, all items are returned.
    """
    if list_ is None: return []
    if len(list_) == 0: return []
    
    sliced_ = list_[starting_index:]
    if ((max_items > 0) and
        (len(sliced_) > max_items)):
        return sliced_[:max_items]
    else:
        return sliced_

    
def remove_list_dupes(list_, max_allowed=1):
    """ removes duplicates from a list object.
        default allowed duplicates is 1, you can allow more if needed.
        minimum allowed is 1. this is not a list deleter.
    """
    
    for item_ in [item_copy for item_copy in list_]:
        while list_.count(item_) > max_allowed:
            list_.remove(item_)
    
    return list_

def prepend_path(prepend_this, prependto_path):
    """ os.path.join fails if prependto_path starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = prepend_path("/view" , project.source_dir)
    """
    
    spath = (prepend_this + prependto_path) if prependto_path.startswith('/') else (prepend_this + '/' + prependto_path)
    return spath.replace("//", '/')

def append_path(appendto_path, append_this):
    """ os.path.join fails if append_this starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = append_path("/view" , project.source_dir)
    """
    
    spath = (appendto_path + append_this) if append_this.startswith('/') else (appendto_path + '/' + append_this)
    return spath.replace("//", '/')



def get_filename(file_path):
    try:
        sfilename = os.path.split(file_path)[1]
    except:
        _log.error("error in os.path.split(" + file_path + ")")
        sfilename = file_path
    return sfilename
    
def safe_arg(_url):
    """ basically just trims the / from the POST args right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
    if s.startswith('/'):
        s = s[1:]
    return s


def trim_special(source_string):
    """ removes all html, and other code related special chars.
        so <tag> becomes tag, and javascript.code("write"); becomes javascriptcodewrite.
        to apply some sort of safety to functions that generate html strings.
        if someone did this: 
            welbornprod.com/blog/tag/<script type="text/javascript">document.write("d");</script>
        you're gonna have a bad time.
    """
    
    special_chars = "<>/.'" + '"' + "#!;:&"
    working_copy = source_string
    for char_ in source_string:
        if char_ in special_chars:
            working_copy = working_copy.replace(char_, '')
    return working_copy

            
def is_file_or_dir(spath):
    """ returns true if path is a file, or is a dir. """
    
    return (os.path.isfile(spath) or os.path.isdir(spath))


def get_browser_name(request):
    """ return the user's browser name """
    
    # get user agent
    user_agent = get_user_agent(request)
    return user_agent.browser.family.lower()
    
def get_browser_style(request):
    """ return browser-specific css file (or False if not needed) """
    
    browser_name = get_browser_name(request)
    # get browser css to use...
    if browser_name.startswith("ie"):
        return "/static/css/main-ie.css"
    elif "firefox" in browser_name:
        return "/static/css/main-gecko.css"
    elif "chrome" in browser_name:
        return "/static/css/main-webkit.css"
    else:
        return False
    
def is_mobile(request):
    """ determine if the client is a mobile phone/tablet
        actually, determine if its not a pc.
    """
    
    if request is None:
        # happens on template errors, which hopefully never make it to production.
        return False
    
    return (not get_user_agent(request).is_pc)


def get_relative_path(spath):
    """ removes base path to make it django-relative.
        if its a '/static' related dir, just trim up to '/static'.
    """
    
    if settings.BASE_DIR in spath:
        spath = spath.replace(settings.BASE_DIR, '')
    
    # if static file, just make it a '/static/...' path.
    if '/static' in spath:
        spath = spath[spath.index('/static'):]
    return spath


def get_absolute_path(relative_file_path):
    """ return absolute path for file, if any
        returns empty string on failure.
        restricted to public STATIC_PARENT dir.
        if no_dir is True, then only file paths are returned.
    """
    
    if relative_file_path == "":
        return ""
    

    #if relative_file_path.startswith('/'): relative_file_path = relative_file_path[1:]
    # Guard against ../ tricks.
    if '..' in relative_file_path:
        return ''
    
    sabsolutepath = ""
    for root, dirs, files in os.walk(settings.STATIC_PARENT): #@UnusedVariable: dirs, files
        spossible = os.path.join(root, relative_file_path)

        # dirs allowed
        if os.path.isfile(spossible) or os.path.isdir(spossible):
            sabsolutepath = spossible
            break
    
    # Guard against files outside of the project.
    if not sabsolutepath.startswith(settings.STATIC_PARENT):
        return ''
    
    return sabsolutepath


def debug_allowed(request):
    """ returns True if the debug info is allowed for this ip/request.
        inspired by debug_toolbar's _show_toolbar() method.
    """
    
    # full test mode, no debug allowed (as if it were the live site.)
    if getattr(settings, 'TEST', False):
        return False
    
    # If user is admin/authenticated we're okay.
    if request.user.is_authenticated() and request.user.is_staff:
        return True
    
    # Non-authenticated users:
    # Get ip for this user
    remote_addr = get_remote_ip(request)
    if not remote_addr:
        return False
    
    # run address through our quick debug security check (settings.INTERNAL_IPS and settings.DEBUG)
    ip_in_settings = (remote_addr in settings.INTERNAL_IPS)
    # log all invalid ips that try to access debug
    if not ip_in_settings:
        ipwarnmsg = 'Debug not allowed for ip: {}'.format(str(remote_addr))
        ipwarnmsg += '\n    ...DEBUG is {}.'.format(str(settings.DEBUG))
        _log.warn(ipwarnmsg)
    return (ip_in_settings and bool(settings.DEBUG))


def get_object_safe(objects_, **kwargs):
    """ does a mymodel.objects.get(kwargs),
        Other Keyword Arguments:

        returns None on error.
    """
    if hasattr(objects_, 'objects'):
        # Main Model passed instead of Model.objects.
        objects_ = getattr(objects_, 'objects')
        
    try:
        obj = objects_.get(**kwargs)
    except:
        # No Error is raised, just return None
        obj = None
    return obj


def get_objects_if(objects_, attribute, equals, orderby=None):
    """ Filters objects, returns only objects with 'attribute' == equals.
        Arguments:
            objects_  : A query set, or my_Model.objects
            attribute : Name of an attribute to check (string to be used with getattr())
            equals    : What the attribute should be to get included.
                        if getattr(object, attribute) == equals: results.append(object)
            orderby   : orderby for django's queryset. all() is used if orderby is None
    """
    
    results = None
    if orderby is None:
        if hasattr(objects_, 'all'):
            fetched = objects_.all()
            try:
                results = [obj for obj in fetched if getattr(obj, attribute) == equals]
            except Exception as ex:
                _log.error("error retrieving results: \n" + str(ex))
                results = None
        else:
            _log.debug(str(objects_) + " has no all()!")
    else:
        if hasattr(objects_, 'order_by'):
            fetched = objects_.order_by(orderby)
            try:
                results = [obj for obj in fetched if getattr(obj, attribute) == equals]
            except Exception as ex:
                _log.error("error retrieving results: \n" + str(ex))
                results = None
        else:
            _log.debug(str(objects_) + " has no order_by()!")
    return results


def get_remote_host(request):
    """ Returns the HTTP_HOST for this user. """
    
    host = request.META.get('REMOTE_HOST', None)
    return host


def get_remote_ip(request):
    """ Just returns the IP for this user (for ip.html, is_debug_allowed(), etc.). """
    # possible ip forwarding, if available use it.
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if x_forwarded_for:
        remote_addr = x_forwarded_for.split(',')[0].strip()
    else:
        remote_addr = request.META.get('REMOTE_ADDR', None)
    return remote_addr
