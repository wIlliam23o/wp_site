""" Welborn Productions - Misc - Search
        Provides functions needed by the searcher app.
    -Christopher Welborn 08-30-14
"""
from misc.models import wp_misc
from misc import misctools


def get_content(miscobj):
    """ Return the full content for a misc object. """
    return misctools.get_long_desc(miscobj)


def get_desc(miscobj):
    """ Returns the description for a misc object for searching and displaying.
    """
    return miscobj.description


def get_objects():
    """ Return all searchable misc objects. """
    return wp_misc.objects.filter(disabled=False)


def get_targets(miscobj, content=None, desc=None):
    """ Get target search strings. """
    content = content or get_content(miscobj)
    desc = desc or get_desc(miscobj)
    return (
        miscobj.name,
        miscobj.alias,
        miscobj.version,
        miscobj.filetype,
        miscobj.language,
        content,
        desc,
        str(miscobj.publish_date)
    )


def result_args(miscobj, desc=None):
    """ Get kwargs needed to create a WpResult. """
    desc = desc or get_desc(miscobj)

    return {
        'title': miscobj.name,
        'desc': desc,
        'link': '/misc/#{}'.format(miscobj.alias),
        'posted': str(miscobj.publish_date),
        'restype': 'Misc.'
    }
