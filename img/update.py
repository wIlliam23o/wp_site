#!/usr/bin/env python3
"""
    Helper for ObjectUpdate, that allows this model to be updated/viewed
    from the command line.
    -Christopher Welborn 1-1-17
"""
from img.models import wp_image
# Model to work with.
model = wp_image
# Name for these models.
name = 'Image'
# Attributes to use for identifiers when looking up an object.
attrs = ('image_id', 'title', 'filename')
# Aliases for this app name,
aliases = ('img', )


def do_list():
    """ List all images. """
    try:
        images = wp_image.objects.order_by('image_id')
    except Exception as ex:
        raise ValueError('Unable to list images!\n{}'.format(ex))
    imglen = len(images)
    print('Found {} image{}:'.format(imglen, '' if imglen == 1 else 's'))
    for i in images:
        print('    {} - {}\n      {}'.format(
            str(i.image_id).ljust(5),
            i.title,
            i.filename)
        )
    return 0


def get_header(obj):
    """ Return a formatted header string, for listing. """
    return '{} - {} ({})'.format(
        obj.image_id,
        (obj.title or '<no title>').strip(),
        obj.filename
    )
