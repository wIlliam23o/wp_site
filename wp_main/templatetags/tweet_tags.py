""" Welborn Productions - Template Tags - Tweet Tags
    ... handles some formatting of tweet data for templates.
"""
import re
from urllib.parse import quote as urlquote
from django.utils.safestring import mark_safe
from django import template
register = template.Library()


def force_size_suffix(n):
    """ Ensure that a size for height/width ends with at least 'px'. """
    if not n:
        return n
    s = str(n)
    if s.lower() == 'auto':
        return 'auto'
    if not s.endswith(('%', 'px')):
        return '{}px'.format(s)

    # Size is fine.
    return n


def format_hashlink_html(hashtag):
    """ Create a link (html string) from a hashtag. """
    hashlinkfmt = 'https://twitter.com/hashtag/{}?src=hash'
    template = '<a href=\'{l}\' target=\'_blank\' title=\'{t}\'>{txt}</a>'

    if hashtag.startswith('#'):
        hashtag = hashtag[1:]

    link = hashlinkfmt.format(urlquote(hashtag))
    withhash = '#{}'.format(hashtag)
    return template.format(l=link, t=hashtag, txt=withhash)


def format_link_html(href, text=None):
    """ Create a link (html string) from just the href. """
    if text is None:
        text = href
        while '://' in text:
            text = text[text.index('://') + 3:]
    template = '<a href=\'{h}\' target=\'_blank\' title=\'{t}\'>{t}</a>'
    return template.format(h=href, t=text)


def format_name_html(name):
    """ Create a link (html string) from just the twitter name. """
    if name.startswith('@'):
        name = name[1:]

    template = (
        '<a href=\'https://twitter.com/{n}\' target=\'_blank\'>@{n}</a>'
    )
    return template.format(n=name)


def format_photo_html(
        src, href=None, height=None, width=None,
        maxheight=None, maxwidth=None):
    """ Create an img tag (html string) from an image href and optional sizes.
        If href is passed, it is wrapped in a link (<a>).
        The whole thing is wrapped in a div.
    """
    divclsname = 'tweet-photo-box'
    imgclsname = 'tweet-photo'
    divtemplate = '<div class=\'{cls}\'>{child}</a>'
    linktemplate = '<a href=\'{href}\' target=\'_blank\'>{child}</a>'
    imgtemplate = '<img class=\'{cls}\' src=\'{src}\'{style}>'

    stylecss = parse_size(
        height=height,
        width=width,
        maxheight=maxheight,
        maxwidth=maxwidth)
    style = ' style=\'{}\''.format(stylecss) if stylecss else ''

    imgtag = imgtemplate.format(cls=imgclsname, src=src, style=style)
    if href is None:
        # Just an image tag.
        return divtemplate.format(cls=divclsname, child=imgtag)

    # Wrap it in a link to the original image.
    linktag = linktemplate.format(href=href, child=imgtag)
    return divtemplate.format(cls=divclsname, child=linktag)


def parse_size(height=None, width=None, maxheight=None, maxwidth=None):
    """ Parse a height and width into css attributes.
        Height and width can be strings or integers, with or without
        % or 'px' added. 'px' will be added if both are missing.
    """
    cssstyle = {
        'height': force_size_suffix(height),
        'width': force_size_suffix(width),
        'max-height': force_size_suffix(maxheight),
        'max-width': force_size_suffix(maxwidth)
    }

    return ';'.join(('{}: {}'.format(k, v) for k, v in cssstyle.items() if v))


@register.filter
def parse_tweet_html(tweetdata):
    """ Parse a single tweets text into an html string.
        ...should replace URLs and HashTags with links.
        If no links or hashtags are found, the original text is returned.
        On success, the resulting HTML for the text is returned.
    """
    if not tweetdata:
        return ''

    origtext = tweetdata.get('text', '')
    if not origtext:
        return origtext

    # Get all entity data (hashtags, links)
    entities = tweetdata.get('entities', {})
    if not entities:
        return tweetdata.get('text', '')

    # Parse links first.
    urls = entities.get('urls', [])
    text = origtext
    for urlinfo in urls:
        urlactual = urlinfo.get('url', None)
        urldisplay = urlinfo.get('display_url', None)
        urlhref = urlinfo.get('expanded_url', None)
        if (urldisplay is None) or (urlhref is None) or (urlactual is None):
            continue
        text = text.replace(urlactual, format_link_html(urlhref, urldisplay))

    words = text.split(' ')
    # Parse names.
    namepat = re.compile('^@(.+)')
    for iword, word in enumerate(words):
        namematch = namepat.match(word)
        if namematch:
            name = namematch.groups()[0]
            words[iword] = format_name_html(name)
    text = ' '.join(words)

    # Parse images.
    media = entities.get('media', [])
    for mediainfo in media:
        mediatype = mediainfo.get('type', None)
        if (not mediatype) or (mediatype != 'photo'):
            # Not handling videos right now.
            continue
        urlactual = mediainfo.get('url', None)
        urlimage = mediainfo.get('media_url', None)
        size = mediainfo.get('sizes', {}).get('medium', {})
        maxheight = size.get('h', None)
        maxwidth = size.get('w', None)
        if (urlactual is None) or (urlimage is None):
            continue
        imghtml = format_photo_html(
            urlimage,
            href=urlactual,
            height=None,
            width='100%',
            maxheight=maxheight,
            maxwidth=maxwidth)

        text = text.replace(urlactual, imghtml)

    # Parse the hashtags in this text (if any are available.)
    # This is hand-rolled because changing the text wrecks hashtag indices
    # ..until I find a better way to use the API data.
    hashpat = re.compile(r'^\#\w+')
    words = text.split(' ')
    for iword, word in enumerate(words):
        if hashpat.match(word):
            words[iword] = format_hashlink_html(word)
    text = ' '.join(words)

    return mark_safe(text)
