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


def is_viewable(miscobj):
    """ Whether or not a View File (locally) button should be used. """
    return misctype_byname(miscobj.filetype).viewable


def get_screenshots(miscobj):
    """ Return screenshots code for this miscobj.
        (if any are available)
    """

    imagedir = misctools.get_screenshots_dir(miscobj)
    if imagedir:
        return mark_safe(htmltools.get_screenshots(imagedir))
    else:
        return None


def get_warning(miscobj):
    """ Return any warning associated with this type. """

    finalwarning = []
    typewarning = misctype_byname(miscobj.filetype).warning
    if typewarning:
        finalwarning.append(typewarning)

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


def has_html_content(miscobj):
    nocontent = ((miscobj.contentfile == '') and
                 (miscobj.contentfile == 'none') and
                 (miscobj.content == ''))
    return not nocontent


def has_screenshots(miscobj):
    """ Returns True if this obj has a screenshots dir.
        Otherwise, False.
    """

    imagedir = misctools.get_screenshots_dir(miscobj)
    return imagedir


def has_warning(miscobj):
    """ Determines whether this object needs a warning attached. """

    typewarning = (misctype_byname(miscobj.filetype).warning is not None)
    langwarning = (miscobj.language in ('Python 2', 'Python 3', 'Python'))
    return (typewarning or langwarning)


def load_html_content(miscobj):
    return misctools.get_long_desc(miscobj)


def processed_content(miscobj):
    """ Process a miscobjs content, highlights and all. """

    content = load_html_content(miscobj)
    if content:
        return process_highlighting(content)
    else:
        return content


def process_highlighting(htmlcontent):
    """ Highlights all code/class=highlight python tags """

    # Turn this into a html_content() object
    # for easy access to helper functions
    html_con = htmltools.html_content(htmlcontent)
    html_con.highlight()
    return mark_safe(html_con.tostring())


# List of registered functions for use with templates
registered = (get_screenshots,
              get_warning,
              has_screenshots,
              has_warning,
              has_html_content,
              is_viewable,
              load_html_content,
              processed_content,
              process_highlighting,
              )

# Register them
for registerfunc in registered:
    register.filter(registerfunc.__name__, registerfunc)
