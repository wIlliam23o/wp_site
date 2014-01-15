'''
    Welborn Productions - misc - Tools
    Holds helpers for misc objects...

Created on Oct 20, 2013

@author: Christopher Welborn
'''

import os

from misc.models import wp_misc
from misc.types import misctype_byname

from wp_main.utilities import htmltools, utilities
from wp_main.utilities.wp_logging import logger

_log = logger('misc.tools').log


def get_long_desc(miscobj):
    """ Gets the long description to use for this wp_misc,
        if contentfile is set, it trys that.
        otherwise it uses .content.
    """

    # Try html file first.
    htmlfile = htmltools.get_html_file(miscobj)
    content = ''
    if htmlfile:
        content = htmltools.load_html_file(htmlfile)

    if not content:
        # Try .content since html content failed.
        content = miscobj.content
        if not content:
            _log.error('Misc object has no content!: {}'.format(miscobj.name))

    return content


def get_misc_warning(miscobj):
    """ Check if this object has warnings associated with it,
        if it does then return the HTML for the warning itself.
    """

    misctype = misctype_byname(miscobj.filetype)
    return misctype.warning


def get_screenshots_dir(miscobj):
    """ Retrieves screenshots html code for this misc object, if
        screenshots are available.
        Otherwise, returns None.
    """

    possibledir = os.path.join('static/images', miscobj.alias)
    imagedir = utilities.get_absolute_path(possibledir)
    if not os.path.isdir(imagedir):
        #_log.debug('No screenshots dir: {}'.format(possibledir))
        return None
    return imagedir


def get_visible_objects():
    """ Get all objects that aren't disabled. """
    try:
        objs = wp_misc.objects.filter(disabled=False).order_by('name')
        return objs
    except wp_misc.DoesNotExist:
        return None


def get_by_identifier(ident):
    """ Retrieve a misc object by Name, Alias, or ID. """
    if not isinstance(ident, (int, float)):
        ident = ident.strip('/')

    def safe_int(i):
        try:
            intval = int(i)
            return intval
        except:
            return i

    #  Methods to try with utilities.get_object_safe
    tryargs = ({'id': safe_int(ident)},
               {'name': ident},
               {'alias': ident})

    for argset in tryargs:
        obj = utilities.get_object_safe(wp_misc, **argset)
        if obj is not None:
            return obj

    # No object found.
    return None


def get_by_filename(filename):
    """ Retrieve a misc object by its file. """

    if filename:
        obj = utilities.get_object_safe(wp_misc, filename=filename)
        if obj:
            return obj
    return None
