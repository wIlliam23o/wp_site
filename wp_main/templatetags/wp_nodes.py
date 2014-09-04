""" Welborn Productions - Template Nodes
    Provides renderable nodes for templates.
    -Christopher Welborn 09-03-14
"""

import os
from django import template
from wp_main.utilities import utilities, htmltools
from wp_main.utilities.wp_logging import logger
_log = logger('templatenodes').log


register = template.Library()


@register.tag
def article_ad(parser, token):
    """ Renders an ArticleAd node in place. """
    return ArticleAd()


@register.tag
def image_viewer(parser, token):
    """ Renders screen shots box, given a path containing images. """
    try:
        tag_name, images_dir = token.split_contents()
    except ValueError:
        errmsg = '{} expects a single argument, a path containing images.'
        tagname = token.contents.split()[0]
        raise template.TemplateSyntaxError(errmsg.format(tagname))
    return ImageViewer(images_dir)


class ArticleAd(template.Node):

    """ Renders an article ad in place. """

    def render(self, context):
        """ Render this article ad node. """
        article_ad = htmltools.render_clean(
            'home/articlead.html',
            context_dict=context)
        return article_ad


class ImageViewer(template.Node):

    """ Renders an image viewer in place, when given an images directory. """

    def __init__(self, images_dir):
        self.images_dir = images_dir

    def render(self, context):
        """ Renders the actual screenshot content when available. """
        try:
            # Using variable path.
            imgdir = template.Variable(self.images_dir).resolve(context)
        except template.VariableDoesNotExist:
            # Using string path.
            imgdir = self.images_dir
            if imgdir.startswith(('"', "'")):
                if not (imgdir[0] == imgdir[-1]):
                    errmsg = 'Mismatched quotes for images_dir in ImageViewer.'
                    _log.error(errmsg)
                    return ''
                else:
                    imgdir = imgdir[1:-1]

        _log.debug('ImageViewer.path: {}'.format(imgdir))
        self.images_dir = imgdir
        content = self.get_images()
        return content if content else ''

    def get_images(self):
        """ Retrieves html formatted images box for all images in
            a directory.
            Returns None on failure.
            Arguments:
                images_dir          : Relative dir containing all the images.
        """
        # accceptable image formats (last 4 chars)
        formats = ('.png', '.jpg', '.gif', '.bmp', 'jpeg')

        # Make sure we are using the right dir.
        # get absolute path for images dir,
        # if none exists then no screenshots are given.
        images_dir = utilities.get_absolute_path(self.images_dir)
        if not images_dir:
            return None

        # Get useable relative dir (user-passed may be wrong format)
        relative_dir = utilities.get_relative_path(images_dir)

        # find acceptable pics
        try:
            all_files = os.listdir(images_dir)
        except Exception as ex:
            _log.debug('Can\'t list dir: {}\n{}'.format(images_dir, ex))
            return None

        # Helper functions for building screenshots.
        relative_img = lambda filename: os.path.join(relative_dir, filename)
        good_format = lambda filename: (filename[-4:] in formats)

        # Build acceptable pics list
        good_pics = [relative_img(f) for f in all_files if good_format(f)]

        # auto-pick noscript image if needed
        if len(good_pics) > 0:
            noscript_image = good_pics[0]
        else:
            # no good pics.
            noscript_image = None

        # Render from template.
        c = {
            'images': good_pics,
            'noscript_image': noscript_image,
        }
        return htmltools.render_clean(
            'home/imageviewer.html',
            context_dict=c)
