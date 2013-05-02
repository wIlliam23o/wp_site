#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - home - tools
     @summary: various functions for home views (latest blog, featured project, news, etc.)
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Apr 1, 2013
'''
# Global DEBUG setting
from django.conf import settings
# Home settings
from home import homesettings as hsettings
# Blog/Projects info
from blogger.models import wp_blog
from projects.models import wp_project
# Local tools
from wp_main.utilities.wp_logging import logger
_log = logger("home.tools").log


def get_latest_blog():
    """ retrieve the last posted blog entry (wp_blog object)"""
    
    return wp_blog.objects.order_by("-posted")[0]


def get_latest_project():
    """ retrieve the last published project (wp_project object) """
    
    return wp_project.objects.order_by("-publish_date")[0]


def get_featured_project():
    """ retrieve the featured project from homesettings 
        as a wp_project object.
        if the project isn't found, we will use the last published
        project.
        returns wp_project object.
    """
    
    salias = hsettings.featured_project_alias
    try:
        # get featured project by alias.
        proj_ = wp_project.objects.get(alias=salias)
    except Exception as ex:
        # bad alias?
        _log.debug("unable to retrieve featured project: " + salias + \
                   '\n' + str(ex))
        proj_ = get_latest_project()
        
    return proj_