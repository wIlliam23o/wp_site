""" Welborn Productions - Projects - Search
        Provides functions needs for the searcher app.
    -Christopher Welborn 08-30-14
"""
from projects.models import wp_project
from projects import tools


def get_content(proj, request=None):
    """ Returns the full content for a project for searching. """
    return tools.get_html_content(proj, request)


def get_desc(proj):
    """ Returns the description for a project for searching and displaying. """
    return proj.description


def get_objects():
    """ Returns searchable projects. """
    return wp_project.objects.filter(disabled=False)


def get_targets(proj, content=None, desc=None):
    """ Returns searchable target strings for a project. """
    content = content or get_content(proj)
    desc = desc or get_desc(proj)
    return (
        proj.name,
        proj.alias,
        proj.version,
        desc,
        content,
        str(proj.publish_date)
    )


def result_args(proj, desc=None):
    """ Returns kwargs needed to create a WpResult. """
    desc = desc or get_desc(proj)
    return {
        'title': '{} v. {}'.format(proj.name, proj.version),
        'desc': desc,
        'link': '/projects/{}'.format(proj.alias),
        'posted': str(proj.publish_date),
        'restype': 'Project'
    }
