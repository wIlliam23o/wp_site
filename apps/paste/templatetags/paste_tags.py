""" Welborn Productions - Apps - Paste - Template Tags
        Provides filters for paste app's templates.
        -Christopher Welborn 2014
"""

from django import template
from wp_main.utilities.wp_logging import logger
from wp_main.utilities.utilities import get_datetime, get_time_since

_log = logger('apps.paste.paste_tags').log

register = template.Library()


def child_count(paste):
    """ Get count of children for this paste. """
    if paste and hasattr(paste, 'children'):
        children = paste.children
        return getattr(children, 'count', lambda: 0)()
    return 0


def paste_time(date, shortdate=False):
    """ Parse a date, and return human readable time-elapsed since the date.
        If it has been more than 1 day, the full Weekday, Month, Day, Time,
        etc. is used.
        Arguments:
            date       : datetime object to evaluate.
            shortdate  : shortdate arg for utilities.get_datetime if used.
    """

    if date is None:
        return date

    since = get_time_since(date)
    if (' day' in since):
        # Not today.
        return get_datetime(date, shortdate=shortdate)

    if not since:
        # Just now.
        return 'just now'

    # Less than 1 day, more than 0.1 seconds.
    return '{} ago'.format(since)


def trim_reply_title(title):
    """ Make sure a paste title is trimmed to fit in the vertical menu. """

    if title and len(title) > 20:
        return '{}...'.format(title[:20])
    return title

registered_filters = (
    child_count,
    paste_time,
    trim_reply_title,
)

# register all filters in the registered tuple.
for filter_ in registered_filters:
    register.filter(filter_.__name__, filter_)
