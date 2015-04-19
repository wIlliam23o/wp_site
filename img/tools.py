""" Welborn Productions - Img - Tools
    Provides utilities for working with the img app.
    -Christopher Welborn 2-5-15
"""
import os.path
from django.conf import settings
from img.models import wp_image


def get_by_filename(abs_path):
    """ Return  wp_image object by absolute filename. """
    if not abs_path:
        return None
    # This will convert the abs path into the image.name.
    fname = abs_path.replace(settings.MEDIA_ROOT, '').strip('/')
    if fname:
        # Get the filename only (from image.name).
        fname = os.path.split(fname)[-1]
    # No 2 images should have the same filename.
    img = wp_image.objects.filter(filename=fname)

    # So return the first element if we have a good list.
    return img[0] if img else None
