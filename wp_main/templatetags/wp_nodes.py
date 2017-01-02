""" Welborn Productions - Template Nodes
    Provides renderable nodes for templates.
    -Christopher Welborn 09-03-14
"""
import base64
import logging
import os
from django import template
from wp_main.utilities import utilities, htmltools, highlighter

log = logging.getLogger('wp.templatenodes')


register = template.Library()


@register.tag(name='acesnippet')
def ace_snippet(parser, token):
    try:
        tagname, elementid, fileext = token.split_contents()
    except ValueError:
        try:
            tagname, elementid = token.split_contents()
            fileext = '.txt'
        except ValueError:
            raise ValueError(
                'Invalid arguments for acesnippet tag: {}'.format(
                    token.contents
                )
            )
    # Grab contents (actually a NodeList) from block.
    # This can be nodelist.render(context)'d to get the text.
    nodelist = parser.parse(('endacesnippet',))
    parser.delete_first_token()
    return AceSnippet(elementid=elementid, fileext=fileext, nodelist=nodelist)


@register.tag
def ad_article(parser, token):
    """ Renders an ArticleAd node in place.
        Replaces soon-to-be-deprecated article_ad
    """

    return AdArticle()


@register.tag
def ad_bottom(parser, token):
    """ Renders the AdBottom node in place.
        A google ad for the bottom of every page.
    """
    return AdBottom()


def b64encode(s):
    """ Encode string as bas64. """
    return base64.encodebytes(s.encode('utf-8')).decode('utf-8').strip()


@register.tag
def fav_icons(parser, token):
    return FavIcons()


@register.tag
def highlight(parser, token):
    """ Highlight code syntax, given a lexer name for pygments and a string.
    """
    try:
        # Try using the full highlight signature.
        tag_name, lang, embedded, code = token.split_contents()
    except ValueError:
        # Try two arguments, embedded = False.
        try:
            tag_name, lang, code = token.split_contents()
            embedded = None
        except ValueError:
            tag_name = token.contents.split()[0]
            errmsg = '{} expects 2 arguments. A lexer name and a string.'
            raise template.TemplateSyntaxError(errmsg.format(tag_name))

    return Highlighter(lexer_name=lang, embedded=embedded, code=code)


@register.tag
def hl(parser, token):
    """ Alias for highlight(). """
    return highlight(parser, token)


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


def parse_arg(value, context):
    """ Parse an argument for template tags. Will try using a context variable,
        but fall back to a string value.
    """
    try:
        parsedvalue = template.Variable(value).resolve(context)
    except template.VariableDoesNotExist:
        return value
    return parsedvalue


@register.tag
def tracking_google(parser, token):
    """ Renders the google tracking code. """
    return TrackingGoogle()


def var_quotes(s, varname=None):
    """ Make sure a string's quotes match.
        Remove quotes from string.
        For parsing Template.Variables.
    """
    if s.startswith(('"', "'")):
        if not (s[0] == s[-1]):
            errmsg = 'Mismatched quotes for \'{}\'!'.format(varname)
            log.error(errmsg)
            raise template.TemplateSyntaxError(errmsg)
        else:
            return s[1:-1]
    # Not a quoted string.
    return s


class AceSnippet(template.Node):
    """ Renders an Ace Editor snippet.
        Usage:
            {% acesnippet "myelementid" ".txt" %}
                content here.
            {% endacesnippet %}
    """
    def __init__(self, elementid=None, fileext=None, nodelist=None):
        self.elementid = elementid
        self.fileext = fileext
        self.nodelist = nodelist

    def render(self, context):
        elementid = parse_arg(self.elementid, context)
        fileext = parse_arg(self.fileext, context)
        text = self.nodelist.render(context).strip()

        context = context or {}
        context.update({
            'elementid': elementid,
            'fileext': fileext,
            'text': b64encode(text) if text else ''
        })

        return htmltools.render_clean('home/acesnippet.html', context=context)


class AdArticle(template.Node):

    """ Renders an article ad in place. """

    def render(self, context):
        """ Render this article ad node. """
        adarticle = htmltools.render_clean(
            'home/ad_article.html',
            context=context)
        return adarticle


class AdBottom(template.Node):

    """ Renders a google ad for the bottom of the page. """

    def render(self, context):
        adbottom = htmltools.render_clean(
            'home/ad_bottom.html',
            context=context)
        return adbottom


class FavIcons(template.Node):

    """ Renders favicons code for many browsers/devices. """

    def render(self, context):
        favs = htmltools.render_clean(
            'home/fav_icons.html',
            context=context)
        return favs


class Highlighter(template.Node):

    """ Renders syntax highlighted code using pygments. """

    def __init__(self, lexer_name=None, embedded=False, code=None):
        self.lexer_name = lexer_name
        self.code = code
        self.embedded = embedded

    def render(self, context):
        """ Render the highlighted code according to the user's lexer name.
        """
        try:
            lexer_name = template.Variable(self.lexer_name).resolve(context)
        except template.VariableDoesNotExist:
            lexer_name = self.lexer_name

        try:
            code = template.Variable(self.code).resolve(context)
        except template.VariableDoesNotExist:
            code = self.code

        if self.embedded:
            try:
                embedded = template.Variable(self.embedded).resolve(context)
            except template.VariableDoesNotExist:
                log.debug('Bad variable for \'embedded\': {}'.format(
                    self.embedded))
                embedded = False
        else:
            embedded = False

        # code = var_quotes(code, varname='Highlighter.code')
        # lexername = var_quotes(lexer_name, varname='Highlighter.lexer_name')

        hl = highlighter.WpHighlighter(
            lexer_name=lexer_name,
            code=code,
            classes=['highlighted-embedded'] if embedded else None)
        content = hl.highlight()
        # log.debug('\n{d}\nHighlighter:\n\n{c}\n{d}\n'.format(
        #     c=content,
        #     d='-' * 80))
        return content


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

        # log.debug('ImageViewer.path: {}'.format(imgdir))
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
        # accceptable image formats
        formats = ('.png', '.jpg', '.gif', '.bmp', '.jpeg')

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
            log.debug('Can\'t list dir: {}\n{}'.format(images_dir, ex))
            return None

        # Build acceptable pics list
        good_pics = [
            os.path.join(relative_dir, f)
            for f in all_files
            if os.path.splitext(f)[-1] in formats
        ]

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
            context=c)


class TrackingGoogle(template.Node):

    """ Renders the google tracking code from the template:
        home/tracking_google.html
    """

    def render(self, context):
        trackingscript = htmltools.render_clean('home/tracking_google.html')
        return trackingscript
