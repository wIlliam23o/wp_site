#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Welborn Productions - Blogger - BlogTools
        Helps to build views/info for blog posts.

    -Christopher Welborn <cj@welbornprod.com> - Mar 20, 2013
'''


# Global settings
from django.conf import settings
from django.template import loader, Template
from django.template.base import TemplateDoesNotExist

# For trimming posts.
import lxml.html

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import htmltools
from wp_main.utilities.wp_logging import logger
_log = logger("blog.tools").log

# Blog Info
from blogger.models import wp_blog

# Fix Python3 (until I remove py2 completely)
if settings.SYSVERSION[0] == '3':
    unicode = str

# Defaults (if nothing is passed to these functions)
DEFAULT_ORDERBY = '-posted_datetime'
# number of posts per page.
DEFAULT_MAXPOSTS = 25
# number of lines before adding 'more..' button on previews.
DEFAULT_MAXLINES = 17
# number of characters before adding 'more..' button on previews.
DEFAULT_MAXLENGTH = 2000


def fix_post_list(blog_posts, **kwargs):
    """ fixes all post.body in a list of posts.
        uses get_post_body to return the correct body to use.
        trims body length to fit maximum allowed for listing.
        trim settings can be disabled by setting to 0. (max_posts=0)

        runs prepare_content on all post.body's for highlighting and whatnot.
        returns list of blog_posts.

        Keyword Arguments:
            max_posts  :  Maximum number of posts to show.
            max_text_length  : Maximum character length before trimming.
            max_text_lines   : Maximum number of lines before trimming.
    """

    if blog_posts is None:
        return []
    max_posts = kwargs.get('max_posts', DEFAULT_MAXPOSTS)
    # max_text_length = kwargs.get('max_text_length', DEFAULT_MAXLENGTH)
    # max_text_lines = kwargs.get('max_text_lines', DEFAULT_MAXLINES)

    # trim posts length
    if ((max_posts > 0) and
            (len(blog_posts) > max_posts)):
        blog_posts = blog_posts[:max_posts]
    return blog_posts


def get_all_tags():
    """ retrieve a list of all tags from all blog posts """

    all_tags = []
    # add up all tags.
    for post_ in wp_blog.objects.filter(disabled=False):
        all_tags.extend(get_tag_list(post_))
    # remove duplicates and return.
    return utilities.remove_list_dupes(all_tags)


def get_post_body(post):
    """ retrieves body for post.
        if html_url is set, we will try to load the file
        if loading fails, or it is not set, we will use post.body.
    """

    if post is None:
        _log.error('post is None!')
        return ''

    template = None
    try:
        slugfile = '{}.html'.format(post.slug)
        template = loader.get_template(slugfile)
        # We are bypassing file lookup, and going straight to template.
        absolute_path = None
    except TemplateDoesNotExist:
        absolute_path = utilities.get_absolute_path(post.html_url)
        if not absolute_path:
            # no valid html_url, using post body as a Template.
            # 'template' overrides the file path in load_html_file.
            template = Template(post.body)

    # load template content.
    scontent = htmltools.load_html_file(
        absolute_path,
        template=template,
        context={
            'post': post
        })
    return scontent


def get_post_body_short(post, max_text_length=None, max_text_lines=None):
    """ retrieves body for post, timming if needed.
        uses get_post_body to retrieve the initial body. """

    if max_text_length is None:
        max_text_length = DEFAULT_MAXLENGTH
    if max_text_lines is None:
        max_text_lines = DEFAULT_MAXLINES
    new_body = get_post_body(post)
    trimmed = False

    # trim by maximum text length
    if ((max_text_length > 0) and
            (len(new_body) > max_text_length)):
        new_body = new_body[:max_text_length]
        trimmed = True

    # trim by maximum lines
    if max_text_lines > 0:
        # Testing actual text content lines using lxml.
        text_content = lxml.html.fromstring(new_body).text_content()
        while '\n\n' in text_content:
            text_content = text_content.replace('\n\n', '\n')
        text_content = text_content.strip()
        if text_content.count('\n') > max_text_lines:
            # needs trimming.
            lines_ = new_body.split('\n')[:max_text_lines + 1]
            new_body = '\n'.join(lines_)
            trimmed = True

    # trim by <br>'s
    if ((max_text_lines > 0) and (new_body.count('<br') > max_text_lines)):
        # needs trimming
        lines_ = new_body.split('<br')[:max_text_lines + 1]
        new_body = '<br'.join(lines_)
        trimmed = True

    # Fix open tags
    new_body = htmltools.fix_open_tags(new_body)

    # post was trimmed? add "...continued" and readmore box.
    if trimmed:
        readmorecontext = {
            'href': '/blog/view/{}'.format(post.slug),
            'nobreak': False,
        }
        readmoretxt = htmltools.render_clean(
            'blogger/readmore.html',
            context=readmorecontext)
        new_body = '\n'.join((
            new_body,
            '<span class=\'continued\'> ...(continued)</span>',
            readmoretxt))

    return new_body


def get_post_byany(_identifier):
    """ retrieve blog post by any identifier, returns None on failure """

    # by id
    try:
        id_ = int(_identifier)
        post_ = utilities.get_object_safe(wp_blog.objects, id=id_)
    except ValueError:
        post_ = None

    # by title
    if post_ is None:
        post_ = utilities.get_object_safe(wp_blog.objects, title=_identifier)

    # by slug
    if post_ is None:
        # id and title failed, try slug.
        # remove html ending
        if _identifier.lower().endswith(".html"):
            _identifier = _identifier[:-5]
        if _identifier.lower().endswith(".htm"):
            _identifier = _identifier[:-4]

        # try quick slug id. (Case-insensitive because all slugs are lowercase)
        post_ = utilities.get_object_safe(wp_blog.objects,
                                          slug=_identifier.lower())

    if post_ is None:
        return post_
    else:
        return post_ if not post_.disabled else None


def get_posts_by_tag(_tag, starting_index=0, max_posts=-1, order_by=None):
    """ retrieve all posts with tag_ as a tag. """

    if order_by is None:
        order_by = DEFAULT_ORDERBY
    if ',' in _tag:
        _tag = _tag.replace(',', ' ')

    _tag = utilities.trim_special(_tag)

    if ' ' in _tag:
        tag_queries = _tag.split(' ')
    else:
        tag_queries = [_tag]

    # get all posts with these tags.
    found = []
    for post_ in wp_blog.objects.order_by(order_by):
        if post_.disabled:
            continue
        post_tags = post_.tags.replace(',', ' ')
        # get list of post tags
        if ' ' in post_tags:
            post_tag_list = post_tags.split(' ')
        else:
            post_tag_list = [post_tags]
        # find tag queries: whole word, case sensative match.
        for tag_name in tag_queries:
            if tag_name in post_tag_list:
                if post_ not in found:
                    found.append(post_)

    # trim for optional pagination.
    return utilities.slice_list(found, starting_index, max_posts)


def get_post_list(starting_index=0, max_posts=None, order_by=None):
    """ returns a list of posts, starting with starting_id,
        as long as max_posts.
        this is for pageination.
    """
    if order_by is None:
        order_by = DEFAULT_ORDERBY
    if max_posts is None:
        max_posts = DEFAULT_MAXPOSTS
    all_posts = wp_blog.objects.filter(disabled=False).order_by(order_by)
    return utilities.slice_list(all_posts, starting_index, max_posts)


def get_tag_links(post):
    """ get links for tags section.
        returns Html string rendered from blogger/taglinks.html template.
    """

    # fix commas
    try:
        ptags = post.tags.replace(',', ' ')
    except Exception as ex:
        _log.error('Error getting post tags for: {}\n{}'.format(post, ex))
        tag_list = []
    else:
        ptags = ptags.replace(',', ' ')
        # make list of tags
        if not ptags:
            tag_list = []
        else:
            tag_list = ptags.split()
        # remove empty items
        while tag_list.count('') > 0:
            tag_list.remove('')

    context = {
        'post': post,
        'tagnames': sorted(tag_list) if tag_list else [],
    }
    return htmltools.render_clean(
        'blogger/taglinks.html',
        context=context)


def get_tag_list(post_object_or_tag_string):
    """ turns tag string into list of tags,
        post object can be passed and we will use its post.tags.
        fixes commas (replaces with spaces before splitting).
        returns list on success, empty list on failure.
    """

    if hasattr(post_object_or_tag_string, 'encode'):
        # tag string was passed
        ptags = post_object_or_tag_string
    else:
        try:
            # post object was passed.
            ptags = post_object_or_tag_string.tags
        except:
            # no valid object passed.
            errfmt = 'Error getting tags from: {}'
            _log.error(errfmt.format(post_object_or_tag_string))
            return []
    # fix commas
    ptags = ptags.replace(',', ' ')
    # make list of tags
    if ptags == "":
        tag_list = []
    else:
        tag_list = ptags.split(" ")
    # remove empty items
    while tag_list.count("") > 0:
        tag_list.remove("")

    return tag_list


def get_tags_post_count():
    """ retrieve the number of posts each tag has.
        returns a dict containing tag_name:count
    """

    tag_counts = {}

    for post in wp_blog.objects.filter(disabled=False):
        tags = get_tag_list(post)
        for tag in tags:
            if tag in tag_counts.keys():
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1

    return tag_counts


def get_tags_fontsizes(tags_dict=None):
    """ returns all tag name with font size according to post count.
        for listing all tags on the tags.html page.
        returns a dict with {tag_name:font size} (in em's)
    """

    if not tags_dict:
        tags_dict = get_tags_post_count()

    sizemap_max = '2em'
    # Sizes adjusted for small post count :) Can be changed later.
    sizemap = {
        (0, 5): '0.7em',
        (4, 10): '0.8em',
        (9, 15): '1em',
        (14, 70): '1.2em',
        (69, 100): '1.4em',
        (99, 200): '1.7em',
    }
    tag_sizes = {}
    # Loop over all tag names, setting their css size.
    for tag_name in tags_dict:
        tag_count = tags_dict[tag_name]
        # Match the tags count with the proper css size.
        for minval, maxval in sizemap:
            sizecss = sizemap[(minval, maxval)]
            if minval < tag_count < maxval:
                # Found the proper range, set it and move to the next tag.
                tag_sizes[tag_name] = sizecss
                break
        else:
            # Count exceeds the current size map, set to max size.
            tag_sizes[tag_name] = sizemap_max
    # Return the map of {tag_name: css_size}
    return tag_sizes


def prepare_content(body_content):
    """ runs various functions on the content, like source-highlighting """

    # do auto source highlighting
    # if "<pre class=" in body_content:
    #    body_content = highlighter.highlight_inline(body_content)
    # body_content = highlighter.highlight_codes(body_content)
    return body_content


class WpTag():

    """ tag class for use with the tags.html template and view. """

    def __init__(self, name=None, count=None, size=None):
        self.name = name or ''
        self.count = count or 0
        self.size = size or '1em'
