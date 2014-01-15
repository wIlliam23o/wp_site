#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welborn productions - home - tools
     @summary: various functions for home views
               (latest blog, featured project, news, etc.)
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Apr 1, 2013
'''
import os
import os.path  # @UnusedImport: os is used.

# Home settings
from home import homesettings as hsettings
# Blog/Projects info
from blogger.models import wp_blog
from projects.models import wp_project
# Local tools
from wp_main.utilities.wp_logging import logger
from wp_main.utilities import utilities

_log = logger("home.tools").log


def get_latest_blog():
    """ retrieve the last posted blog entry (wp_blog object)"""
    
    for post in wp_blog.objects.order_by('-posted_datetime'):
        if post.disabled:
            continue
        return post
    return None


def get_latest_project():
    """ retrieve the last published project (wp_project object) """
    
    try:
        proj = wp_project.objects.order_by('-publish_date').first()
    except Exception as ex:
        _log.error('Unable to retrieve first():\n{}'.format(ex))
        return None
    return proj


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
        _log.debug("unable to retrieve featured project: " + salias +
                   '\n' + str(ex))
        proj_ = get_latest_project()
        
    return proj_


def get_scriptkid_image():
    """ returns a random image filename from /images/scriptkid """
    
    import random
    image_dir = utilities.get_absolute_path("images/scriptkids")
    goodexts = ("jpeg", ".jpg", ".png", ".gif", ".bmp")
    try:
        images = [img for img in os.listdir(image_dir)
                  if img[-4:].lower() in goodexts]
    except Exception as ex:
        _log.error("can't do listdir() on: " + image_dir + '\n' + str(ex))
        return None
    if not images:
        _log.error("images was empty!")
        return None
    
    randomindex = random.randint(0, len(images) - 1)
    return os.path.join(image_dir, images[randomindex])


class StatsInfo(object):

    """ Holds info for stats.html template and home.view_stats() view. """

    def __init__(self, title=None, statlines=None):
        self.title = title
        self.statlines = statlines


class StatsCollection(object):

    """ Holds a collection of StatsInfo objects. """

    def __init__(self, *args):
        """ Adds a list of StatsInfo()'s on intialization """
        self.stats = []
        for arg in args:
            if arg is not None:
                self.stats.append(arg)

    def add(self, statsinfo):
        self.stats.append(statsinfo)
