'''misc.templatetags.misc_tags
    
    Welborn Productions - Misc - Tags
    Handles template tags for Misc objects/views
    Created on Oct 20, 2013

@author: Christopher Welborn
'''
import os.path

from django import template
from django.utils.safestring import mark_safe
from wp_main.utilities.wp_logging import logger
from wp_main.utilities.htmltools import html_content

from misc.tools import get_long_desc



_log = logger('misc_tags').log


def has_html_content(miscobj):
    nocontent = ((miscobj.contentfile == '') and (miscobj.contentfile == 'none') and (miscobj.content == ''))
    return not nocontent

def load_html_content(miscobj):
    return get_long_desc(miscobj)

def processed_content(miscobj):
    """ Process a miscobjs content, highlights and all. """
    
    content = load_html_content(miscobj)
    if content:
        return process_highlighting(content)
    else:
        return content
    
def process_highlighting(htmlcontent):
    """ Highlights all code/class=highlight python tags """
    
    # Turn this into a html_content() object for easy access to helper functions
    html_con = html_content(htmlcontent)
    html_con.highlight()
    return mark_safe(html_con.tostring())

    
