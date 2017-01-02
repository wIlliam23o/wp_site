#!/usr/bin/env python3
"""
    Helper for ObjectUpdate, that allows this model to be updated/viewed
    from the command line.
    -Christopher Welborn 1-1-17
"""
from misc.models import wp_misc
# Model to work with.
model = wp_misc
# Name for these models.
name = 'Misc'
# Attributes to use for identifiers when looking up an object.
attrs = ('name', 'alias', 'version')
# Aliases for this app name,
aliases = ('miscellaneous', )


def do_list():
    """ List all project  names/aliases/versions. """

    try:
        projs = [p for p in wp_misc.objects.order_by('alias')]
    except Exception as ex:
        raise ValueError('Unable to list misc objects!\n{}'.format(ex))
    if not projs:
        raise ValueError('No misc objects found!')

    # Instead of doing max(len()) on the misc objects twice, just iterate once
    # and update both longestname and longestalias.
    # longestname = max(len(p.name) for p in projs))
    # longestalias = max(len(p.alias) for p in projs))
    longestname = 0
    longestalias = 0
    for p in projs:
        paliaslen = len(p.alias)
        pnamelen = len(p.name)
        if paliaslen > longestalias:
            longestalias = paliaslen
        if pnamelen > longestname:
            longestname = pnamelen

    projlen = len(projs)
    print('Found {} misc object{}:'.format(
        projlen,
        '' if projlen == 1 else 's'
    ))
    infostrfmt = '    {name} ({alias}) [{marker}] {ver} {filename}'
    for proj in projs:
        versionstr = 'v. {}'.format(proj.version) if proj.version else ''
        infostrargs = {
            'name': str(proj.name).ljust(longestname),
            'marker': 'D' if proj.disabled else 'E',
            'alias': str(proj.alias).ljust(longestalias),
            'ver': versionstr,
            'filename': str(proj.filename),
        }
        infostr = infostrfmt.format(**infostrargs)
        print(infostr)
    return 0


def get_header(obj):
    """ Return a formatted header string, for listing. """
    return '{} ({}) v. {}'.format(obj.name, obj.alias, obj.version)
