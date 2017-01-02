#!/usr/bin/env python3
"""
    Helper for ObjectUpdate, that allows this model to be updated/viewed
    from the command line.
    -Christopher Welborn 1-1-17
"""
from downloads.models import file_tracker
# Model to work with.
model = file_tracker
# Name for these models.
name = 'File Tracker'
# Attributes to use for identifiers when looking up an object.
attrs = ('image_id', 'title', 'filename')
# Aliases for this app name,
aliases = ('file', 'dl', 'tracker', 'downloads')


def do_list():
    """ List all filetrackers """

    try:
        files = [f for f in file_tracker.objects.order_by('filename')]
    except Exception as ex:
        raise ValueError('Unable to list file trackers!\n{}'.format(ex))

    if not files:
        raise ValueError('No file trackers found!')
    filelen = len(files)
    print('Found {} file tracker{}:'.format(
        filelen,
        '' if filelen == 1 else 's'
    ))
    for f in files:
        print('    {}'.format(f.filename))
    return 0


def get_header(obj):
    """ Return a formatted header string, for listing. """
    return str(obj.filename)
