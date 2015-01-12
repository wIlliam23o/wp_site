""" Welborn Productions - Stats - Tools
    Tools for gathering info about other models and their counts.
    (downloads, views, etc.)
"""


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
