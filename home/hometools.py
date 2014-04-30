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
from apps.models import wp_app

# Local tools
from wp_main.utilities.wp_logging import logger
from wp_main.utilities import utilities

_log = logger('home.tools').log


def get_featured_app():
    """ retrieve the featured web app from homesettings
        as a wp_app object.
        if the app isn't found, return None.
    """

    appalias = hsettings.featured_app_alias
    try:
        app = wp_app.objects.get(alias=appalias)
    except Exception as ex:
        _log.error('Unable to retrieve featured app: '
                   '{}\n{}'.format(appalias, ex))
        return None
    
    return app


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
        proj = wp_project.objects.get(alias=salias)
    except Exception as ex:
        # bad alias?
        _log.error('Unable to retrieve featured project: '
                   '{}\n{}'.format(salias, ex))
        proj = get_latest_project()
        
    return proj


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
