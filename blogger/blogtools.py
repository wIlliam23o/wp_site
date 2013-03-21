#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: blog tools for welborn productions site
     @summary: helps to build views/info for blog posts.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 20, 2013
'''
from django.utils.safestring import mark_safe

from wp_main import utilities
from wp_main.wp_logging import logger
from blogger.models import wp_blog
_log = logger("welbornprod.blog.tools", use_file=True)

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
        _log.debug("get_post_body: no html url, using post.body.")
        # no valid html_url
        return post_.body
    
    # load html file content
    _log.debug("get_post_body: loading html content from " + absolute_path)
    scontent = utilities.load_html_file(absolute_path)
    return scontent


def fix_post_list(blog_posts, max_posts=25, max_text_length=250, max_text_lines=17):
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
            new_body += utilities.readmore_box('/blog/view/' + post_.slug)
        # set new body.
        post_.body = mark_safe(prepare_content(new_body))
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
        from viewer.highlighter import highlight_inline
        body_content = highlight_inline(body_content)
    if "highlight-embedded" in body_content:
        from viewer.highlighter import highlight_embedded
        body_content = highlight_embedded(body_content)
    return body_content


def get_posts_by_tag(_tag):
    """ retrieve all posts with tag_ as a tag. """
    
    if ' ' in _tag:
        tag_queries = _tag.split(' ')
    else:
        tag_queries = [_tag]
    
    found = []
    for post_ in wp_blog.objects.order_by('-posted'):
        for tag_name in tag_queries:
            if tag_name.lower() in post_.tags.lower():
                found.append(post_)
    
    return found


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
        
