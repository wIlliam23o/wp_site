from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

#from projects import models
from blogger.models import wp_blog
# Global settings (for getting absolute path)
from django.conf import settings
# logging capabilities
import logging
_log = logging.getLogger("welbornprod.blog")

# welborn productions utilities
from wp_main import utilities

def index(request):
    """ index list of all blog posts """

    # load blog posts...
    try:
        blog_posts = wp_blog.objects.order_by('-posted')
        
    except:
        _log.error("No blog posts found!")
        blog_posts = False
    # load template
    tmp_blog = loader.get_template("blogger/index.html")
    # load context
    cont_blog = Context({'blog_posts': blog_posts,
                         'extra_style_link': utilities.get_browser_style(request)})
    return HttpResponse(tmp_blog.render(cont_blog))


def view_post(request, _identifier):
    """ view a post by identifier.
        identifier can be:
            pk (id)
            slug
            title
    """
    
    post_ = get_post_byany(_identifier)
    
    if post_ is None:
        _log.error("Post not found: " + _identifier)
        response = utilities.alert_message("Sorry, I can't find that post.",
                                           "<a href='/blog'><span>Click here to go back to the blog index.</span></a>")
    else:
        # build blog post.
        
        # get short title for window-text
        if len(post_.title) > 20:
            post_title_short = ".." + post_.title[len(post_.title) - 30:]
        else:
            post_title_short = post_.title
        
        # get date.
        post_date = post_.posted
        
        # get tags (and format them)
        post_tags = get_tag_links(post_)
            
        # get content for post.
        post_body = get_post_body(post_)
        
        if post_body == "":
            response = utilities.alert_message("Sorry, no content found for this post.",
                                               "<a href='/blog'><span>Click here to go back to the blog index.</span></a>")
        else:
            # prepare content (do highlighting)
            post_body = prepare_content(post_body)
            
            # Build clean HttpResponse with post template...
            response = utilities.clean_response("blogger/post.html",
                                                {'extra_style_link': utilities.get_browser_style(request),
                                                 'extra_style_link2': "/static/css/highlighter.css",
                                                 'post_title_short': post_title_short,
                                                 'post_title': post_.title,
                                                 'post_date': post_date,
                                                 'post_tags': mark_safe(post_tags),
                                                 'post_body': mark_safe(post_body),
                                                 })
        return response

def view_tags(request):
    """ list all posts by tags (categories) """
    
    return HttpResponse("You are looking for all tags.")


def view_tag(request, _tag):
    """ list all posts with these tags """
    
    return HttpResponse("You are looking for this tag: " + _tag)


def no_identifier(request):
    """ returns a message when user forgets to add an identifier """
    
    return HttpResponse("You forgot to add an identifier, maybe you meant to visit /blog/?")


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
    
    # fix commas
    ptags = post_.tags.replace(',', ' ')
    # make list of tags
    ltags = ptags.split(" ")
    
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