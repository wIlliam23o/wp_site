""" Welborn Productions - Img - Search
    Provides an interface for the search app to use when searching images.
    -Christopher Welborn 2-9-15
"""

from img.models import wp_image


def get_content(img, request=None):
    """ Images have no content (no text content) """
    return None


def get_desc(img):
    return img.description


def get_objects():
    """ Only public/enabled images are searchable (even for admins) """
    return wp_image.objects.filter(disabled=False, private=False)


def get_targets(img, content=None, desc=None):
    """ Return the searchable strings for an image. """
    if desc is None:
        desc = get_desc(img)

    return (
        img.title,
        img.filename,
        img.album,
        desc,
        str(img.publish_date)
    )


def result_args(img, desc=None):
    """ Returns arguments needed to build a WpResult from the searcher app. """
    if desc is None:
        desc = get_desc(img)

    return {
        'title': img.title,
        'desc': desc,
        'link': '/img?id={}'.format(img.image_id),
        'posted': str(img.publish_date.date()) if img.publish_date else '?',
        'restype': 'Image'
    }
