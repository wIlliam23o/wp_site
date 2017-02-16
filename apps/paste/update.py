#!/usr/bin/env python3
"""
    Helper for ObjectUpdate, that allows this model to be updated/viewed
    from the command line.
    -Christopher Welborn 1-1-17
"""
from collections import namedtuple
from apps.paste.models import wp_paste, repr_header

# For an implementation of the 'pastetree' script (when listing pastes)
IterPasteResult = namedtuple('IterPasteResult', ['level', 'paste'])

# Model to work with.
model = wp_paste
# Name for these models.
name = 'Paste'
# Attributes to use for identifiers when looking up an object.
attrs = ('publish_date', 'paste_id', 'title')
# Aliases for this app name,
aliases = ('pst', )


def do_list():
    """ List all pastes (in a tree, like the pastetree script). """
    pastecnt = 0
    print(repr_header())
    for pasteresult in iter_pastes():
        indention = '  ' * pasteresult.level
        print('{}{!r}'.format(indention, pasteresult.paste))
        pastecnt += 1

    if pastecnt == 0:
        raise ValueError('No pastes found!')
    print('\nFound {} paste{}.'.format(
        pastecnt,
        '' if pastecnt == 1 else 's',
    ))
    return 0


def get_header(obj):
    """ Return a formatted header string, for listing. """
    return str(obj.filename)


def iter_paste_children(paste, level=1):
    """ Iterate over all children of a paste, and children's children. """
    for p in paste.children.order_by('publish_date'):
        yield IterPasteResult(level, p)
        if p.children.count() > 0:
            yield from iter_paste_children(p, level=level + 1)


def iter_pastes(startpastes=None):
    """ Iterate over all pastes that have no parent.
        Given a 'startpastes' list, it will start from that paste only.
    """
    if startpastes is None:
        pastes = wp_paste.objects.filter(parent=None)
        pastes = pastes.order_by('publish_date')
    else:
        pastes = [startpastes]

    for p in pastes:
        yield IterPasteResult(0, p)
        if p.children.count() > 0:
            yield from iter_paste_children(p, level=1)
