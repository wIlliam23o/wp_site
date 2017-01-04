""" Welborn Productions - Apps - Paste - Template Tags
        Provides filters for paste app's templates.
        -Christopher Welborn 2014
"""

import logging
from django import template

from apps.paste import pastetools

log = logging.getLogger('wp.apps.paste.paste_tags')

register = template.Library()


@register.filter
def child_count(paste):
    """ Get count of children for this paste. """
    if paste and hasattr(paste, 'children'):
        # No content needed for the count.
        return (
            pastetools.get_paste_children(paste, order_by=None)
            .defer('content')
            .count()
        )
    return 0


@register.filter
def is_expired(paste):
    """ Return true if this paste is expired. """
    if hasattr(paste, 'is_expired'):
        return paste.is_expired()
    log.error('Not a paste, missing is_expired method: {!r}'.format(paste))
    return False


@register.filter
def needs_line_breaks(paste):
    """ Return true if this pastes content is long and has no line breaks. """
    if (not paste) or (not paste.content):
        return False
    return (len(max(paste.content.split('\n'))) > 80)


@register.filter
def paste_children(paste):
    """ Makes paste.children available in the templates, after passing
        through a gauntlet of checks (disabled, private, is_expired()).
    """
    return pastetools.get_paste_children(paste)


@register.filter
def paste_parent(paste):
    """ Makes paste.parent available in the template, after passing
        through a gauntlet of checks (disabled, private, is_expired()).
    """
    return pastetools.get_paste_parent(paste)


@register.filter
def trim_reply_title(title):
    """ Make sure a paste title is trimmed to fit in the vertical menu. """

    if title and len(title) > 20:
        return '{}...'.format(title[:20])
    return title
