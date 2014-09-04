""" Welborn Productions - Template Nodes
    Provides renderable nodes for templates.
    -Christopher Welborn 09-03-14
"""

import os
from django import template
from wp_main.utilities import utilities, htmltools, highlighter
from wp_main.utilities.wp_logging import logger
_log = logger('templatenodes').log


register = template.Library()


@register.tag
def article_ad(parser, token):
    """ Renders an ArticleAd node in place. """
    return ArticleAd()


@register.tag
def highlight(parser, token):
    """ Highlight code syntax, given a lexer name for pygments and a string.
    """
    try:
        tag_name, lang, code = token.split_contents()
    except ValueError:
        tag_name = token.contents.split()[0]
        errmsg = '{} expects 2 arguments. A lexer name and a string.'
        raise template.TemplateSyntaxError(errmsg.format(tag_name))
    return Highlighter(lexer_name=lang, code=code)


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


def var_quotes(s, varname=None):
    """ Make sure a string's quotes match.
        Remove quotes from string.
        For parsing Template.Variables.
    """
    if s.startswith(('"', "'")):
        if not (s[0] == s[-1]):
            errmsg = 'Mismatched quotes for \'{}\'!'.format(varname)
            _log.error(errmsg)
            raise template.TemplateSyntaxError(errmsg)
        else:
            return s[1:-1]
    # Not a quoted string.
    return s


class ArticleAd(template.Node):

    """ Renders an article ad in place. """

    def render(self, context):
        """ Render this article ad node. """
        article_ad = htmltools.render_clean(
            'home/articlead.html',
            context_dict=context)
        return article_ad


class Highlighter(template.Node):

    """ Renders syntax highlighted code using pygments. """

    def __init__(self, lexer_name=None, code=None):
        self.lexer_name = lexer_name
        self.code = code

    def render(self, context):
        """ Render the highlighted code according to the user's lexer name. """
        try:
            lexer_name = template.Variable(self.lexer_name).resolve(context)
        except template.VariableDoesNotExist:
            lexer_name = self.lexer_name

        try:
            code = template.Variable(self.code).resolve(context)
        except template.VariableDoesNotExist:
            code = self.code
        code = var_quotes(code, varname='Highlighter.code')
        lexername = var_quotes(lexer_name, varname='Highlighter.lexer_name')

        hl = highlighter.WpHighlighter(lexer_name=lexer_name, code=code)
        return hl.highlight()


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
            imgdir = var_quotes(
                self.images_dir,
                varname='ImageViewer.images_dir')

        #_log.debug('ImageViewer.path: {}'.format(imgdir))
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
