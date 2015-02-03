""" Welborn Productions - Apps - Paste - Template Tags
        Provides filters for paste app's templates.
        -Christopher Welborn 2014
"""

from django import template
from wp_main.utilities.wp_logging import logger
from wp_main.utilities.utilities import get_time_since

_log = logger('apps.paste.paste_tags').log

register = template.Library()


@register.filter
def child_count(paste):
    """ Get count of children for this paste. """
    if paste and hasattr(paste, 'children'):
        children = paste.children
        return getattr(children, 'count', lambda: 0)()
    return 0


@register.filter
def needs_line_breaks(paste):
    """ Return true if this pastes content is long and has no line breaks. """
    if (not paste) or (not paste.content):
        return False
    return (len(max(paste.content.split('\n'))) > 80)


@register.filter
def paste_children(paste):
    """ Makes paste.children available in the templates. """
    c = [p for
         p in paste.children.filter(disabled=False).order_by('-publish_date')]
    return c


@register.filter
def trim_reply_title(title):
    """ Make sure a paste title is trimmed to fit in the vertical menu. """

    if title and len(title) > 20:
        return '{}...'.format(title[:20])
    return title
