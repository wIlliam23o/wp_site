""" Welborn Productions - Img - Template Tags
    Provides template tags for the img app's templates.
    -Christopher Welborn 2-5-15
"""

from django import template

register = template.Library()


@register.filter
def download_url(img):
    """ Returns the /dl url needed to track the download of this image. """
    if not img:
        return ''
    return '/dl/static/media/{}'.format(img.image.name)
