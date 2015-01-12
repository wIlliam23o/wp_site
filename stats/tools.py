""" Welborn Productions - Stats - Tools
    Tools for gathering info about other models and their counts.
    (downloads, views, etc.)
"""

from wp_main.utilities import wp_logging
_log = wp_logging.logger('stats.tools').log


def validate_orderby(modelobj, orderby):
    """ Make sure this orderby is valid for this modelobj.
        It knows about the  '-orderby' style.
        Returns True if the orderby is good, else False.
    """

    try:
        tempobj = modelobj.objects.create()
    except Exception as ex:
        if hasattr(modelobj, '__name__'):
            mname = modelobj.__name__
        else:
            mname = 'unknown model'
        errmsg = '\nUnable to create temp object for: {}\n{}'
        _log.error(errmsg.format(mname, ex))
        return None
    if orderby.startswith('-'):
        orderby = orderby.strip('-')
    goodorderby = hasattr(tempobj, orderby)
    tempobj.delete()
    return goodorderby


class StatsGroup(object):

    """ Holds a collection of stats with a name (Projects, Posts, etc.)
        Each item in .stats will be a StatsItem().
    """

    def __init__(self, name=None, stats=None):
        self.name = name or 'Unknown'
        self.stats = stats or []


class StatsItem(object):

    """ A single item with a name, download_count, and view_count. """

    def __init__(self, name=None, download_count=None, view_count=None):
        self.name = name
        self.download_count = 0 if download_count is None else download_count
        self.view_count = 0 if view_count is None else view_count
