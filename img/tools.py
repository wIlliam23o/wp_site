""" Welborn Productions - Img - Tools
    Provides utilities for working with the img app.
    -Christopher Welborn 2-5-15
"""

from django.conf import settings
from img.models import wp_image


def get_by_filename(abs_path):
    """ Return  wp_image object by absolute filename. """
    if not abs_path:
        return None

    fname = abs_path.replace(settings.MEDIA_ROOT, '').strip('/')
    # No 2 images should have the same filename.
    img = wp_image.objects.filter(filename=fname)
    # So return the first element if we have a good list.
    return img[0] if img else None
