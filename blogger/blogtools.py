#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welborn productions - blogger - blogtools
     @summary: helps to build views/info for blog posts.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 20, 2013
'''


# Global settings
from django.conf import settings
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import htmltools
from wp_main.utilities.wp_logging import logger
_log = logger("blog.tools").log
# Viewer/Highlighter
from wp_main.utilities import highlighter
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


def get_post_list(starting_index=0, max_posts=None, _order_by=None):
    """ returns a list of posts, starting with starting_id,
        as long as max_posts. 
        this is for pageination.
    """
    if _order_by is None:
        _order_by = DEFAULT_ORDERBY
    if max_posts is None:
        max_posts = DEFAULT_MAXPOSTS
    all_posts = wp_blog.objects.filter(disabled=False).order_by(_order_by)
    return utilities.slice_list(all_posts, starting_index, max_posts)
    
    
def get_post_body(post_):
    """ retrieves body for post.
        if html_url is set, we will try to load the file
        if loading fails, or it is not set, we will use post.body.
    """
    
    # TODO: Html content needs to be tied into template render.
    #       see: htmltools.load_html_file(), projects.tools.get_html_content(),
    #            misc.tools.get_long_desc()
    if post_ is None:
        _log.error("post_ = None!")
        return ""
    
    absolute_path = utilities.get_absolute_path(post_.html_url)
    if absolute_path == "":
        # no valid html_url
        return post_.body
    
    # load html file content
    scontent = htmltools.load_html_file(absolute_path)
    return scontent


def get_post_body_short(post_, max_text_length=None, max_text_lines=None):
    """ retrieves body for post, timming if needed.
        uses get_post_body to retrieve the initial body. """

    if max_text_length is None:
        max_text_length = DEFAULT_MAXLENGTH
    if max_text_lines is None:
        max_text_lines = DEFAULT_MAXLINES
    new_body = get_post_body(post_)
    trimmed = False
    
    # trim by maximum text length
    if ((max_text_length > 0) and
       (len(new_body) > max_text_length)):
        new_body = new_body[:max_text_length]
        trimmed = True
        
    # trim by maximum lines
    if ((max_text_lines > 0) and (new_body.count('\n') > max_text_lines)):
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
        new_body += "<span class='continued'> ...(continued)</span>" + \
                    htmltools.readmore_box('/blog/view/' + post_.slug)

    return new_body


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
    max_text_length = kwargs.get('max_text_length', DEFAULT_MAXLENGTH)
    max_text_lines = kwargs.get('max_text_lines', DEFAULT_MAXLINES)

    # TODO: This needs to be done in the template, or somewhere else.
    #      Creating a copy of every post just to trim it later is not
    #      efficient. We need to operate on the original posts,
    #      with a generator or something if we can.
    for post_ in [post_copy for post_copy in blog_posts]:
        new_body = get_post_body_short(post_, max_text_length, max_text_lines)
        # set new body.
        post_.body = new_body
        
    # trim posts length
    if ((max_posts > 0) and
       (len(blog_posts) > max_posts)):
        blog_posts = blog_posts[:max_posts]
    return blog_posts


def get_tag_links(post_):
    """ get links for tags section.
        returns Html string.
    """
    
    snotags = ("<div class='blog-post-tag-link-box'>"
               "<span class='blog-post-tag-link-text'>"
               "None"
               "</span>"
               "</div>")
    # no post.
    if post_ is None:
        return snotags
    # no tags.
    if post_.tags == "":
        return snotags
    
    ltags = get_tag_list(post_.tags)
    
    sbase = """<div class='blog-post-tag-link-box'>
                <a href='/blog/tag/{{ link_name }}'>
                    <span class='blog-post-tag-link-text'>
                        {{ link_name }}
                    </span>
                </a>
              </div>
            """
    # build tag links code
    taglinks = ""
    for tag_ in ltags:
        taglinks += sbase.replace("{{ link_name }}", tag_)
    return taglinks


def prepare_content(body_content):
    """ runs various functions on the content, like source-highlighting """
    
    # do auto source highlighting
    if "<pre class=" in body_content:
        body_content = highlighter.highlight_inline(body_content)
    body_content = highlighter.highlight_codes(body_content)
    return body_content


def get_posts_by_tag(_tag, starting_index=0, max_posts=-1, _order_by=None):
    """ retrieve all posts with tag_ as a tag. """
    
    if _order_by is None:
        _order_by = DEFAULT_ORDERBY
    if ',' in _tag:
        _tag = _tag.replace(',', ' ')
        
    _tag = utilities.trim_special(_tag)
    
    if ' ' in _tag:
        tag_queries = _tag.split(' ')
    else:
        tag_queries = [_tag]
    
    # get all posts with these tags.
    found = []
    for post_ in wp_blog.objects.order_by(_order_by):
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
                if not post_ in found:
                    found.append(post_)
    
    # trim for optional pagination.
    return utilities.slice_list(found, starting_index, max_posts)


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
            _log.error("error getting tags from a " +
                       str(post_object_or_tag_string) +
                       " object!")
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


def get_all_tags():
    """ retrieve a list of all tags from all blog posts """
    
    all_tags = []
    # add up all tags.
    for post_ in wp_blog.objects.filter(disabled=False):
        all_tags += get_tag_list(post_)
    # remove duplicates and return.
    return utilities.remove_list_dupes(all_tags)


def get_tags_post_count():
    """ retrieve the number of posts each tag has.
        returns a dict containing tag_name:count
    """
    
    tag_counts = {}
    
    for post_ in wp_blog.objects.filter(disabled=False):
        tags = get_tag_list(post_)
        for tag_ in tags:
            if tag_ in tag_counts.keys():
                tag_counts[tag_] += 1
            else:
                tag_counts[tag_] = 1
            
    return tag_counts
    

def get_tags_fontsizes(tags_dict=None):
    """ returns all tag name with font size according to post count.
        for listing all tags on the tags.html page.
        returns a dict with {tag_name:font size} (in em's)
    """
    
    if not tags_dict:
        tags_dict = get_tags_post_count()
    
    tag_sizes = {}
    for tag_name in tags_dict.keys():
        tag_count = tags_dict[tag_name]
        if tag_count < 10:
            tag_sizes[tag_name] = "0.7em"
        elif 9 < tag_count < 30:
            tag_sizes[tag_name] = "0.8em"
        elif 29 < tag_count < 50:
            tag_sizes[tag_name] = "1em"
        elif 49 < tag_count < 70:
            tag_sizes[tag_name] = "1.2em"
        elif 69 < tag_count < 100:
            tag_sizes[tag_name] = "1.4em"
        elif 99 < tag_count < 200:
            tag_sizes[tag_name] = "1.7em"
        elif 199 < tag_count:
            tag_sizes[tag_name] = "2em"
            
    return tag_sizes


class wp_tag():

    """ tag class for use with the tags.html template and view. """

    def __init__(self, name_="", count_=0, size_="1em"):
        self.name = name_
        self.count = count_
        self.size = size_
