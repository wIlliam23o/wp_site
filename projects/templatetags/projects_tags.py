#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Projects - Template Tags
     @summary: Provides extra functionality to templates in the projects app.
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 31, 2013
'''

from django import template
from django.utils.safestring import mark_safe #, mark_for_escaping
from projects import tools as ptools
from wp_main.utilities.wp_logging import logger
import os.path

_log = logger("projects.tags").log

register = template.Library()

def process_project_html(project):
    """ runs the project through some html processing
        for screenshots, article ads, download code, sourceview code, etc.
        works on project.get_html_content() through projects.tools.process_injections()
    """
    if project is None: 
        _log.debug("received None project!")
        return ""
    
    try:
        proj_html = ptools.process_injections(project)
    except Exception as ex:
        _log.debug("Error processing injections:\n" + str(ex))
        return ""
    else:
        return mark_safe(proj_html)


def has_project_html(project):
    """ test to see if project has a valid html file to load. """
    
    return os.path.isfile(ptools.get_html_file(project))


# Registered tags
registered = [process_project_html,
              has_project_html]
# Register all tags in the 'registered list'
for func in registered:
    register.filter(func.func_name, func)