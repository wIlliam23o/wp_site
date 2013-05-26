#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
          project: utilities.py
         @summary: various tools/utilities for the welbornproductions.net django site..
    
          @author: Christopher Welborn <cj@welbornproductions.net>
    @organization: welborn productions <welbornproductions.net>
"""

import os.path
from os import walk #@UnusedImport: os.walk is used, aptana is stupid.
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
    
    sabsolutepath = ""
    for root, dirs, files in os.walk(settings.STATIC_PARENT): #@UnusedVariable: dirs, files
        spossible = os.path.join(root, relative_file_path)
        # dirs allowed
        if os.path.isfile(spossible) or os.path.isdir(spossible):
            sabsolutepath = spossible
            break
    
    return sabsolutepath


def debug_allowed(request):
    """ returns True if the debug info is allowed for this ip/request.
        inspired by debug_toolbar's _show_toolbar() method.
    """
    
    # full test mode, no debug allowed.
    if getattr(settings, 'TEST', False):
        return False

    # possible ip forwarding, if available use it.
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if x_forwarded_for:
        remote_addr = x_forwarded_for.split(',')[0].strip()
    else:
        remote_addr = request.META.get('REMOTE_ADDR', None)

    # run address through our quick debug security check (settings.INTERNAL_IPS and settings.DEBUG)
    # future settings may have a different or seperate list of debug-allowed ip's.
    ip_in_settings = (remote_addr in settings.INTERNAL_IPS)
    
    return (ip_in_settings and bool(settings.DEBUG))
      
