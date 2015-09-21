#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welborn productions - project tools
     @summary: provides tools for building html content related to projects

      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>

   start date: Mar 14, 2013
'''
import logging
import os

# Project info
from projects.models import wp_project
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import htmltools

# Logging
log = logging.getLogger('wp.projects.tools')


def sorted_projects(sort_method="-publish_date"):
    """ return sorted list of projects.
        sort methods: date, name, id
    """

    if sort_method.startswith("date") or sort_method.startswith("-date"):
        sort_method = "-publish_date"

    return [p for p in wp_project.objects.all().order_by(sort_method)
            if not p.disabled]


def get_screenshots_dir(project):
    """ determine screenshots directory for project """
    if project.screenshot_dir == "":
        # try default location
        aliasdir = 'static/images/{}'.format(project.alias)
        images_dir = utilities.get_absolute_path(aliasdir)
    else:
        if os.path.isdir(project.screenshot_dir):
            # project path was absolute
            images_dir = project.screenshot_dir
        else:
            # needs absolute?
            images_dir = utilities.get_absolute_path(project.screenshot_dir)
    return images_dir


def get_html_file(project):
    """ finds html file to use for project content, if any
        returns empty string on failure.
    """

    if project.html_url == "":
        # use default location if no manual override is set.
        aliashtml = 'static/html/{}.html'.format(project.alias)
        html_file = utilities.get_absolute_path(aliashtml)
    elif project.html_url.lower() == 'none':
        # html files can be disabled by putting None in the html_url field.
        return ""
    else:
        if os.path.isfile(project.html_url):
            # already absolute
            html_file = project.html_url
        else:
            # try absolute path
            html_file = utilities.get_absolute_path(project.html_url)
    return html_file


def get_html_content(project, request):
    """ retrieves extra html content for project, if any """

    filename = '{}.html'.format(project.alias)
    content = htmltools.load_html_file(
        filename,
        request=request,
        context={
            'project': project,
        })

    if not content:
        log.debug('Missing html for {}: {}'.format(project.name, filename))

    return content


def get_project_from_path(file_path):
    """ determines if this file is from a project.
        returns project object if it is.
        returns None on failure.
    """

    # check all project names
    for proj in [p for p in wp_project.objects.all() if not p.disabled]:
        if proj.alias in str(file_path):
            return proj
    return None
