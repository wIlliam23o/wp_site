""" Welborn Productions - Apps - Paste - Search
        Provides functions needed for the searcher app.
    -Christopher Welborn 08-30-14
"""

from apps.paste.models import wp_paste

# Disable paste searching for now. -Cj
disabled = True


def get_content(paste):
    """ Returns searchable content for a paste. """
    return paste.content


def get_desc(paste):
    """ Returns paste description for searching and displaying. """
    return paste.title


def get_objects():
    """ Returns searchable pastes. """
    return wp_paste.objects.filter(disabled=False, private=False)


def get_targets(paste, content=None, desc=None):
    """ Returns searchable target strings for pastes. """
    content = content or get_content(paste)
    desc = desc or get_desc(paste)

    return (
        paste.author,
        desc,
        content,
        paste.language,
        paste.paste_id,
        str(paste.publish_date)
    )


def result_args(paste, desc=None):
    """ Returns kwargs needed to create a WpResult. """
    author = paste.author or 'an anonymous author'
    lang = paste.language or 'plain text'
    return {
        'title': paste.title,
        'desc': '...a paste by {} in {}.'.format(author, lang),
        'link': '/paste/?id={}'.format(paste.paste_id),
        'posted': str(paste.publish_date),
        'restype': 'Paste'
    }
