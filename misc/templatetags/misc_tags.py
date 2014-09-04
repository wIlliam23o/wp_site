'''misc.templatetags.misc_tags

    Welborn Productions - Misc - Tags
    Handles template tags for Misc objects/views
    Created on Oct 20, 2013

@author: Christopher Welborn
'''

from django import template
from django.utils.safestring import mark_safe
from wp_main.utilities.wp_logging import logger
from wp_main.utilities import htmltools

from misc import tools as misctools
from misc.types import misctype_byname


register = template.Library()

_log = logger('misc_tags').log


@register.filter
def is_viewable(miscobj):
    """ Whether or not a View File (locally) button should be used. """
    return misctype_byname(miscobj.filetype).viewable


@register.filter
def get_content(miscobj):
    return mark_safe(misctools.get_long_desc(miscobj))


@register.filter
def get_screenshots(miscobj):
    """ Return screenshots code for this miscobj.
        (if any are available)
    """

    imagedir = misctools.get_screenshots_dir(miscobj)
    if imagedir:
        return mark_safe(htmltools.get_screenshots(imagedir))
    else:
        return None


@register.filter
def get_warning(miscobj):
    """ Return any warning associated with this type. """

    finalwarning = []
    typewarning = misctype_byname(miscobj.filetype).warning
    if typewarning:
        finalwarning.append(typewarning.replace('\n', '<br>'))

    langwarnings = {'Python': ('This is known to work with Python 2 and 3.'),
                    'Python 2': ('This has been tested with Python 2, but it '
                                 'won\'t work with Python 3.'),
                    'Python 3': ('This has been tested with Python 3, but it '
                                 'won\'t work with Python  2.'),
                    }
    if miscobj.language in langwarnings.keys():
        finalwarning.append(langwarnings[miscobj.language])

    if len(finalwarning) > 1:
        return mark_safe('<br><br>'.join(finalwarning))
    else:
        return finalwarning[0] if finalwarning else ''


@register.filter
def has_html_content(miscobj):
    nocontent = (
        ((miscobj.contentfile == '') or (miscobj.contentfile == 'none')) and
        (miscobj.content == ''))
    return not nocontent


@register.filter
def has_screenshots(miscobj):
    """ Returns True if this obj has a screenshots dir.
        Otherwise, False.
    """

    imagedir = misctools.get_screenshots_dir(miscobj)
    return imagedir


@register.filter
def has_warning(miscobj):
    """ Determines whether this object needs a warning attached. """

    typewarning = (misctype_byname(miscobj.filetype).warning is not None)
    langwarning = (miscobj.language in ('Python 2', 'Python 3', 'Python'))
    return (typewarning or langwarning)


@register.filter
def misctype_str(miscobj):
    """ Retrieves proper description for this Misc objects filetype. """

    return misctype_byname(miscobj.filetype).description
