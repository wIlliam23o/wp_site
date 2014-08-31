""" Welborn Productions - Apps - Search
        Provides functions needed for the searcher app.
    -Christopher Welborn 08-30-14
"""

from apps.models import wp_app


def get_content(app):
    """ Returns None, apps don't have content. """
    return None


def get_desc(app):
    """ Returns app description for searching and displaying. """
    return app.description


def get_objects():
    """ Returns searchable apps. """
    return wp_app.objects.filter(disabled=False).order_by('-publish_date')


def get_targets(app, content=None, desc=None):
    """ Returns searchable target strings for apps. """
    desc = desc or get_desc(app)
    return (
        app.name,
        app.alias,
        app.version,
        desc,
        str(app.publish_date)
    )


def result_args(app, desc=None):
    """ Returns kwargs needed to create a WpResult. """
    desc = desc or get_desc(app)
    return {
        'title': app.name,
        'desc': desc,
        'link': '/apps/{}'.format(app.alias),
        'posted': str(app.publish_date),
        'restype': 'Web App.'
    }
