#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Welborn Productions - Blogger - BlogTools
        Helps to build views/info for blog posts.

    -Christopher Welborn <cj@welbornprod.com> - Mar 20, 2013
'''

import logging

# For trimming posts.
import lxml.html

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import htmltools
# Blog Info
from blogger.models import wp_blog
log = logging.getLogger('wp.blog.tools')


# Defaults (if nothing is passed to the listing functions)
DEFAULT_ORDERBY = '-posted_datetime'
# Number of posts per page.
DEFAULT_MAXPOSTS = 25
# Number of lines before adding 'read more..' button on previews.
DEFAULT_MAXLINES = 17
# Number of characters before adding 'read more..' button on previews.
# This is not used for blog posts anymore.
DEFAULT_MAXLENGTH = 2000


def add_read_more(content, url, nobreak=False):
    """ Add a 'read more...' button to some content, by rendering the
        blogger/readmore.html template and appending it to the content.
    """
    return '\n'.join((
        content,
        '<span class=\'continued\'> ...(continued)</span>',
        htmltools.render_clean(
            'blogger/readmore.html',
            context={'href': url, 'nobreak': nobreak},
        ),
    ))


def fix_post_list(blog_posts, **kwargs):
    """ fixes all post.body in a list of posts.
        uses get_post_body to return the correct body to use.
        trims body length to fit maximum allowed for listing.
        trim settings can be disabled by setting to 0. (max_posts=0)

        returns list of blog_posts.

        Keyword Arguments:
            max_posts  :  Maximum number of posts to show.
            max_text_length  : Maximum character length before trimming.
            max_text_lines   : Maximum number of lines before trimming.
    """

    if blog_posts is None:
        return []
    max_posts = kwargs.get('max_posts', DEFAULT_MAXPOSTS)

    # trim posts length
    if ((max_posts > 0) and (len(blog_posts) > max_posts)):
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
        log.error('post is None!')
        return ''

    # Try for automatic slug-based html file.
    slugfile = '{}.html'.format(post.slug)
    content = htmltools.load_html_template(slugfile)
    if content:
        return content

    # Try the posts's html_url as a template.
    absolute_path = utilities.get_absolute_path(post.html_url)
    if absolute_path:
        # Load the html_url template content.
        return htmltools.load_html_file(
            absolute_path,
            context={
                'post': post
            })

    # No valid html_url, using post body as a Template.
    return htmltools.render_html_str(post.body, context={'post': post})


def get_post_body_short(post, max_text_length=None, max_text_lines=None):
    """ Retrieves body for post using get_post_body, trimming if needed.
        Returns the post's content, possibly with an added 'read more' button.
    """

    if max_text_length is None:
        max_text_length = DEFAULT_MAXLENGTH or 0
    if max_text_lines is None:
        max_text_lines = DEFAULT_MAXLINES or 0
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
        if ('<noscript>' in new_body) and ('</noscript>' not in new_body):
            # Tidylib has failed before.
            new_body = '\n'.join((new_body, '</noscript>'))
        return add_read_more(new_body, 'blogger/view/{}'.format(post.slug))

    return new_body


def get_post_byany(identifier):
    """ retrieve blog post by any identifier, returns None on failure """

    # by id
    try:
        postid = int(identifier)
        post = utilities.get_object_safe(wp_blog.objects, id=postid)
    except ValueError:
        post = None

    # by title
    if post is None:
        post = utilities.get_object_safe(wp_blog.objects, title=identifier)

    # by slug
    if post is None:
        # id and title failed, try slug.
        # remove html ending
        if identifier.lower().endswith('.html'):
            identifier = identifier[:-5]
        if identifier.lower().endswith('.htm'):
            identifier = identifier[:-4]

        # try quick slug id. (Case-insensitive because slugs are lowercase)
        post = utilities.get_object_safe(
            wp_blog.objects,
            slug=identifier.lower())

    if post is None:
        return post

    return post if not post.disabled else None


def get_posts_by_tag(tag, starting_index=0, max_posts=-1, order_by=None):
    """ Retrieve all non-disaabled posts with a certain tag.
        Returns a list of wp_blog.
        Arguments:
                      tag  : Tag to search for (str).
            starting_index : Index to start list at (triming for pagination).
                 max_posts : Maximum length for post list (for pagination).
                  order_by : How to order the posts (DEFAULT_ORDERBY).
    """

    if order_by is None:
        order_by = DEFAULT_ORDERBY
    if ',' in tag:
        tag = tag.replace(',', ' ')

    tag = utilities.trim_special(tag)
    tag_queries = tag.split()

    # get all posts with these tags.
    found = []
    for post in wp_blog.objects.filter(disabled=False).order_by(order_by):
        post_tags = post.tags.replace(',', ' ')
        # get list of post tags
        post_tag_list = post_tags.split()

        # find tag queries: whole word, case sensative match.
        for tag_name in tag_queries:
            if (tag_name in post_tag_list) and (post not in found):
                found.append(post)

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
        log.error('Error getting post tags for: {}\n{}'.format(post, ex))
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
            log.error(errfmt.format(post_object_or_tag_string))
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


def get_tags():
    """ Retrieve a list of all WpTags, with counts and font sizes for each.
    """
    # build list of tags and info for tags.html template
    return [
        WpTag(name=name, count=count)
        for name, count in get_tags_count().items()
    ]


def get_tags_count():
    """ Retrieve the number of posts each tag has.
        Returns a dict containing {'tag_name': count}
    """

    tag_counts = {}

    for post in wp_blog.objects.filter(disabled=False):
        tags = get_tag_list(post)
        for tag in tags:
            existingcnt = tag_counts.get(tag, 0)
            tag_counts[tag] = existingcnt + 1

    return tag_counts


class WpTag():

    """ tag class for use with the tags.html template and view. """
    # Maximum font size for a tag.
    sizemax = '2.0em'
    # Mininum font size for a tag.
    sizemin = '0.7em'
    # Font sizes for count ranges.
    sizemap = {
        (0, 5): '0.7em',
        (4, 10): '0.8em',
        (9, 15): '1em',
        (14, 70): '1.2em',
        (69, 100): '1.4em',
        (99, 200): '1.7em',
    }

    def __init__(self, name=None, count=None, size=None):
        # The tag string (name).
        self.name = name or ''
        # Number of times this tag has been used.
        self.count = count or 0
        # Font size, set manually or automatically by count.
        self.size = size if (size is not None) else self.get_fontsize(count)

    def get_fontsize(self, count):
        """ Get the appropriate font size for a tag, based on count. """
        if count < 0:
            # Should never happen. :P
            return self.sizemin
        for rangeargs in self.sizemap:
            if count in range(*rangeargs):
                return self.sizemap[rangeargs]
        return self.sizemax
