#!/usr/bin/env python
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
_log = logger("welbornprod.blog.tools", use_file=(not settings.DEBUG))
# Viewer/Highlighter
from viewer.highlighter import highlight_inline, highlight_embedded
# Blog Info
from blogger.models import wp_blog


def get_post_byany(_identifier):
    """ retrieve blog post by any identifier, returns None on failure """
    
    try:
        id_ = int(_identifier)
        post_ = wp_blog.objects.get(id=id_)
    except:
        post_ = None
    
    if post_ is None:
        try:
            post_ = wp_blog.objects.get(title=_identifier)
        except:
            post_ = None
    if post_ is None:
        # id and title failed, try slug.
        # remove html ending
        if (_identifier.lower().endswith(".html") or
            _identifier.lower().endswith(".htm")):
            _identifier = _identifier[:_identifier.index(".")]
        try:
            post_ = wp_blog.objects.get(slug=_identifier)
        except:
            post_ = None
    return post_

def get_post_list(starting_index=0, max_posts=-1, _order_by="-posted"):
    """ returns a list of posts, starting with starting_id,
        as long as max_posts. 
        this is for pageination.
    """
    
    all_posts = wp_blog.objects.order_by(_order_by)
    
    return utilities.slice_list(all_posts, starting_index, max_posts)
    
    
def get_post_body(post_):
    """ retrieves body for post.
        if html_url is set, we will try to load the file
        if loading fails, or it is not set, we will use post.body.
    """
    
    if post_ is None:
        _log.error("get_post_body: post_ = None!")
        return ""
    
    absolute_path = utilities.get_absolute_path(post_.html_url)
    if absolute_path == "":
        #_log.debug("get_post_body: no html url, using post.body.")
        # no valid html_url
        return post_.body
    
    # load html file content
    #_log.debug("get_post_body: loading html content from " + absolute_path)
    scontent = htmltools.load_html_file(absolute_path)
    return scontent


def get_post_body_short(post_, max_text_length=0, max_text_lines=17):
    """ retrieves body for post, timming if needed.
        uses get_post_body to retrieve the initial body. """

    new_body = get_post_body(post_)
    trimmed = False
    
    # trim by maximum text length        
    if ((max_text_length > 0) and 
        (len(new_body) > max_text_length)):
        new_body = new_body[:max_text_length]
        trimmed = True
        
    # trim by maximum lines
    if ((max_text_lines > 0) and 
        ('\n' in new_body)):
        lines_ = new_body.split('\n')
        # needs trimming.
        if len(lines_) > max_text_lines:
            lines_ = lines_[:max_text_lines + 1]
            new_body = '\n'.join(lines_)
            trimmed = True
    # post was trimmed? add readmore box.
    if trimmed:
        new_body += htmltools.readmore_box('/blog/view/' + post_.slug)

    
    return new_body


def fix_post_list(blog_posts, max_posts=25, max_text_length=0, max_text_lines=17):
    """ fixes all post.body in a list of posts.
        uses get_post_body to return the correct body to use.
        trims body length to fit maximum allowed for listing.
        trim settings can be disabled by setting to 0. (max_posts=0)
        
        runs prepare_content on all post.body's for highlighting and whatnot.
        returns list of blog_posts.
    """
    
    if blog_posts is None:
        return []
    
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
    
    snotags = "<div class='blog-post-tag-link-box'><span class='blog-post-tag-link-text'>None</span></div>"
    # no post.
    if post_ is None:
        return snotags
    # no tags.
    if post_.tags == "":
        return snotags
    
    ltags = get_tag_list(post_.tags)
    
    sbase = """<div class='blog-post-tag-link-box'>
                <a href='/blog/tag/{{ link_name }}'>
                    <span class='blog-post-tag-link-text'>{{ link_name }}</span>
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
        body_content = highlight_inline(body_content)
    if "highlight-embedded" in body_content:
        body_content = highlight_embedded(body_content)
    return body_content


def get_posts_by_tag(_tag, starting_index=0, max_posts=-1, _order_by='-posted'):
    """ retrieve all posts with tag_ as a tag. """
    
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
    
    if (isinstance(post_object_or_tag_string, str) or
        isinstance(post_object_or_tag_string, unicode)):
        # tag string was passed
        ptags = post_object_or_tag_string
    else:
        try:
            # post object was passed.
            ptags = post_object_or_tag_string.tags
        except:
            # no valid object passed.
            _log.error("get_tag_list: error getting tags from a " + str(post_object_or_tag_string) + " object!")
            return []
    # fix commas
    ptags = ptags.replace(',', ' ')
    # make list of tags
    if ptags == "":
        return []
    else:
        return ptags.split(" ")
    
    
def get_all_tags():
    """ retrieve a list of all tags from all blog posts """
    
    all_tags = []
    # add up all tags.
    for post_ in wp_blog.objects.all():
        all_tags += get_tag_list(post_)
    # remove duplicates and return.
    return utilities.remove_list_dupes(all_tags)


def get_tags_post_count():
    """ retrieve the number of posts each tag has.
        returns a dict containing tag_name:count
    """
    
    tag_counts = {}
    
    for post_ in wp_blog.objects.all():
        tags = get_tag_list(post_)
        for tag_ in tags:
            if tag_counts.has_key(tag_):
                tag_counts[tag_] += 1
            else:
                tag_counts[tag_] = 1
            
    return tag_counts
    

def get_tags_fontsizes(tags_dict = None):
    """ returns all tag name with font size according to post count.
        for listing all tags on the tags.html page.
        returns a dict with {tag_name:font size} (in em's)
    """
    
    if tags_dict is None:
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
