#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - robots - main
     @summary: provide a robots.txt file
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Apr 9, 2013
'''
from django.views.decorators.cache import never_cache
from wp_main.utilities import responses


@never_cache
def view_robots_blockall(request):
    """ block all pages """
    
    return responses.text_response("User-agent: *\nDisallow: /")


@never_cache
def view_robots_any(request):
    """ allow any page """
    
    return responses.text_response("User-agent: *\nAllow: /")


@never_cache
def view_byserver(request):
    """ decide which robots.txt to serve up based on current server.
        currently blocks all for any servername starting with 'test.'
    """
    
    server_name = request.META["SERVER_NAME"]
    
    if server_name.startswith("test."):
        return view_robots_blockall(request)
    else:
        # normal robots, allow all.
        return view_robots_any(request)
