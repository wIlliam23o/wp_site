#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
          project: utilities.py
         @summary: various tools/utilities for Welborn Prod.
    
          @author: Christopher Welborn <cj@welbornprod.com>
    @organization: welborn productions <welbornprod.com>
"""

import os
import sys
import traceback
from datetime import datetime

# global settings
from django.conf import settings
# User-Agent helper...
from wp_user_agents.utils import get_user_agent  # @UnresolvedImport

# use log wrapper for debug and file logging.
from wp_main.utilities.wp_logging import logger
_log = logger("utilities").log


def append_path(appendto_path, append_this):
    """ os.path.join fails if append_this starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = append_path("/view" , project.source_dir)
    """
    
    if append_this.startswith('/'):
        spath = (appendto_path + append_this)
    else:
        spath = (appendto_path + '/' + append_this)
    return spath.replace("//", '/')

           
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
    
    # run address through our quick debug security check
    # (settings.INTERNAL_IPS and settings.DEBUG)
    ip_in_settings = (remote_addr in settings.INTERNAL_IPS)
    # log all invalid ips that try to access debug
    if settings.DEBUG and (not ip_in_settings):
        ipwarnmsg = 'Debug not allowed for ip: {}'.format(str(remote_addr))
        ipwarnmsg += '\n    ...DEBUG is {}.'.format(str(settings.DEBUG))
        _log.warn(ipwarnmsg)
    return (ip_in_settings and bool(settings.DEBUG))


def get_absolute_path(relative_file_path):
    """ return absolute path for file, if any
        returns empty string on failure.
        restricted to public STATIC_PARENT dir.
        if no_dir is True, then only file paths are returned.
    """
    
    if relative_file_path == "":
        return ""
    
    # Guard against ../ tricks.
    if '..' in relative_file_path:
        return ''
    
    sabsolutepath = ''
    # Remove '/static' from the file path.
    if relative_file_path.startswith(('static', '/static')):
        staticparts = relative_file_path.split('/')
        if len(staticparts) > 1:
            staticstart = 2 if relative_file_path.startswith('/') else 1
            staticpath = '/'.join(staticparts[staticstart:])
            # use new relative path (without /static)
            relative_file_path = staticpath
        else:
            # Don't allow plain '/static'
            return ''

    # Walk real static dir.
    for root, dirs, files in os.walk(settings.STATIC_ROOT):  # noqa
        spossible = os.path.join(root, relative_file_path)
        if os.path.exists(spossible):
            sabsolutepath = spossible
            break

    # Guard against files outside of the public /static dir.
    if not sabsolutepath.startswith(settings.STATIC_ROOT):
        return ''
    
    return sabsolutepath


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
        return "/static/css/main-ie.min.css"
    elif "firefox" in browser_name:
        return "/static/css/main-gecko.min.css"
    elif "chrome" in browser_name:
        return "/static/css/main-webkit.min.css"
    else:
        return False
    

def get_datetime(date=None, shortdate=False):
    """ Return date/time string.
        Arguments:
            date       : Existing datetime object to format.
                         Default: datetime.now()
            shortdate  : Return date part in short format (m-d-yyyy)
                         Default: False
    """
    if date is None:
        date = datetime.now()
    if shortdate:
        return date.strftime('%m-%d-%Y %I:%M%S %p')
    return date.strftime('%A %b. %d, %Y %I:%M:%S %p')


def get_date(date=None, shortdate=False):
    """ Return date string.
        Arguments:
            date       : Existing datetime object to format.
                         Default: datetime.now()
            shortdate  : Return date in short format (m-d-yyyy)
                         Default: False
    """
    if date is None:
        date = datetime.now()
    if shortdate:
        return date.strftime('%m-%d-%Y')
    return date.strftime('%A %b. %d, %Y')


def get_filename(file_path):
    try:
        sfilename = os.path.split(file_path)[1]
    except Exception:
        _log.error('error in os.path.split({})'.format(file_path))
        sfilename = file_path
    return sfilename
    

def get_objects_enabled(objects_):
    """ Safely retrieves all objects where disabled == False.
        Handles 'no objects', returns [] if there are no objects.
    """
    
    # Model was passed instead of model.objects.
    if hasattr(objects_, 'objects'):
        objects_ = getattr(objects_, 'objects')
    
    try:
        allobjs = objects_.filter(disabled=False)
    except Exception as ex:
        _log.error('No objects to get!: {}\n{}'.format(objects_.__name__, ex))
        allobjs = None
    
    return allobjs

    
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
    except Exception:
        # No Error is raised, just return None
        obj = None
    return obj
    
# Alias for function.
get_object = get_object_safe


def get_relative_path(spath):
    """ removes base path to make it django-relative.
        if its a '/static' related dir, just trim up to '/static'.
    """
    
    if not spath:
        return ''

    prepend = ''
    if settings.STATIC_ROOT in spath:
        spath = spath.replace(settings.STATIC_ROOT, '')
        prepend = '/static'
    elif settings.BASE_PARENT in spath:
        spath = spath.replace(settings.BASE_PARENT, '')
    if spath and (not spath.startswith('/')):
        spath = '/{}'.format(spath)

    if prepend:
        spath = '{}{}'.format(prepend, spath)

    return spath


def get_remote_host(request):
    """ Returns the HTTP_HOST for this user. """
    
    host = request.META.get('REMOTE_HOST', None)
    return host


def get_remote_ip(request):
    """ Just returns the IP for this user
        (for ip.html, debug_allowed(), etc.)
    """
    # possible ip forwarding, if available use it.
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if x_forwarded_for:
        remote_addr = x_forwarded_for.split(',')[0].strip()
    else:
        remote_addr = request.META.get('REMOTE_ADDR', None)
    return remote_addr


def get_server(request):
    """ Return the current server/hostname for a request. """
    if not request:
        return None

    try:
        meta = request.META
    except AttributeError as exatt:
        _log.error('Unable to retrieve META from request:\n'
                   '{}'.format(exatt))
        return None

    tryattrs = (
        'SERVER_NAME',
        'HTTP_X_FORWARDED_SERVER',
        'HTTP_HOST',
        'HTTP_X_FORWARDED_HOST',
    )
    for attr in tryattrs:
        server = meta.get(attr, None)
        if server is not None:
            return server

    # None of those attributes were filled out in request.META.
    return None


def get_time(time=None, shorttime=False):
    """ Return time string.
        Arguments:
            time       : Existing datetime object to format.
                         Default: datetime.now()
            shorttime  : Return time in short format (without am/pm)
                         Default: False
    """
    if time is None:
        time = datetime.now()
    if shorttime:
        return time.strftime('%I:%M:%S')
    return time.strftime('%I:%M:%S %p')


def get_time_since(date, humanform=True):
    """ Parse a datetime object,
        return human-readable time-elapsed.
    """
    
    secs = (datetime.now() - date).total_seconds()
    if secs < 60:
        if humanform:
            # Right now.
            if secs < 0.1:
                return ''
            # Seconds (decimal format)
            return '{:0.1f} seconds'.format(secs)
        else:
            # Seconds only.
            return '{:0.1f}s'.format(secs)

    minutes = secs / 60
    seconds = int(secs % 60)
    minstr = 'minute' if int(minutes) == 1 else 'minutes'
    secstr = 'second' if seconds == 1 else 'seconds'
    if minutes < 60:
        # Minutes and seconds only.
        if humanform:
            if seconds == 0:
                # minutes
                return '{} {}'.format(int(minutes), minstr)
            # minutes, seconds
            fmtstr = '{} {}, {} {}'
            return fmtstr.format(int(minutes), minstr, seconds, secstr)
        else:
            # complete minutes, seconds
            fmtstr = '{}m:{}s'
            return fmtstr.format(int(minutes), seconds)

    hours = minutes / 60
    minutes = int(minutes % 60)
    hourstr = 'hour' if int(hours) == 1 else 'hours'
    minstr = 'minute' if minutes == 1 else 'minutes'
    if hours < 24:
        # Hours, minutes, and seconds only.
        if humanform:
            if minutes == 0:
                # hours
                return '{} {}'.format(int(hours), hourstr)
            # hours, minutes
            fmtstr = '{} {}, {} {}'
            return fmtstr.format(int(hours), hourstr, minutes, minstr)
        else:
            # complete hours, minutes, seconds
            fmtstr = '{}h:{}m:{}s'
            return fmtstr.format(int(hours), hourstr, minutes, seconds)

    days = int(hours / 24)
    hours = int(hours % 24)
    # Days, hours
    daystr = 'day' if days == 1 else 'days'
    hourstr = 'hour' if hours == 1 else 'hours'
    if humanform:
        if hours == 0:
            # days
            return '{} {}'.format(days, daystr)
        # days, hours
        fmtstr = '{} {}, {} {}'
        return fmtstr.format(days, daystr, hours, hourstr)
    else:
        # complete days, hours, minutes, seconds
        fmtstr = '{}d:{}h:{}m:{}s'
        return fmtstr.format(days, hours, minutes, seconds)


def is_file_or_dir(spath):
    """ returns true if path is a file, or is a dir. """
    
    return (os.path.isfile(spath) or os.path.isdir(spath))


def is_mobile(request):
    """ determine if the client is a mobile phone/tablet
        actually, determine if its not a pc.
    """
    
    if request is None:
        # happens on template errors,
        # which hopefully never make it to production.
        return False
    
    return (not get_user_agent(request).is_pc)


def logtraceback(log=None, message=None):
    """ Log the latest traceback.
        Arguments:
            log      : Function that accepts a string as its first argument.
                       If None is passed, print() will be used.
                       The idea is to use myloggingobject.error.
            message  : Optional additional message to log.

        Returns a list of all lines logged.
    """
    typ, val, tb = sys.exc_info()
    tbinfo = traceback.extract_tb(tb)
    linefmt = ('Error in:\n'
               '  {fname}, {funcname}(),\n'
               '    line {num}: {txt}\n'
               '    {typ}:\n'
               '      {msg}')
    if log is None:
        log = print

    logged = []
    for filename, lineno, funcname, txt in tbinfo:
        # Build format() args from the tb info.
        fmtargs = {
            'fname': filename,
            'funcname': funcname,
            'num': lineno,
            'txt': txt,
            'typ': typ,
            'msg': val,
        }
        # Report the error.
        if message is None:
            logmsg = linefmt.format(**fmtargs)
        else:
            logmsg = '{}\n{}'.format(message, linefmt.format(**fmtargs))
        log(logmsg)
        logged.append(logmsg)
    return logged


def prepend_path(prepend_this, prependto_path):
    """ os.path.join fails if prependto_path starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = prepend_path("/view" , project.source_dir)
    """
    
    if prependto_path.startswith('/'):
        spath = (prepend_this + prependto_path)
    else:
        spath = (prepend_this + '/' + prependto_path)
    return spath.replace("//", '/')


def remove_list_dupes(list_, max_allowed=1):
    """ removes duplicates from a list object.
        default allowed duplicates is 1, you can allow more if needed.
        minimum allowed is 1. this is not a list deleter.
    """
    
    for item_ in [item_copy for item_copy in list_]:
        while list_.count(item_) > max_allowed:
            list_.remove(item_)
    
    return list_


def safe_arg(_url):
    """ basically just trims the / from the POST args right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
    if s.startswith('/'):
        s = s[1:]
    return s


def slice_list(list_, starting_index=0, max_items=-1):
    """ slice a list starting at: starting index.
        if max_items > 0 then only that length of items is returned.
        otherwise, all items are returned.
    """
    if list_ is None:
        return []
    if len(list_) == 0:
        return []
    
    sliced_ = list_[starting_index:]
    if ((max_items > 0) and
       (len(sliced_) > max_items)):
        return sliced_[:max_items]
    else:
        return sliced_


def trim_special(source_string):
    """ removes all html, and other code related special chars.
        so <tag> becomes tag, and javascript.code("write"); 
        becomes javascriptcodewrite.
        to apply some sort of safety to functions that generate html strings.
        incase someone did this (all one line): 
            welbornprod.com/blog/tag/<script type="text/javascript">
                document.write("d");
            </script>
    """
    
    special_chars = "<>/.'" + '"' + "#!;:&"
    working_copy = source_string
    for char_ in source_string:
        if char_ in special_chars:
            working_copy = working_copy.replace(char_, '')
    return working_copy
