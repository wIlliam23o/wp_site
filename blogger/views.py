from django.http import HttpResponse
#from django.template import Context, loader
#from django.utils.safestring import mark_safe # don't escape html with strings marked safe.


from blogger.models import wp_blog
from blogger import blogtools

# Global settings (for getting absolute path)
#from django.conf import settings
# logging capabilities
from wp_main.wp_logging import logger
_log = logger("welbornprod.blog", use_file=True)

# welborn productions utilities
from wp_main import utilities

def index(request):
    """ index list of all blog posts """

    # load blog posts...
    try:
        blog_posts = blogtools.fix_post_list(wp_blog.objects.order_by('-posted'),
                                             max_text_lines=16)
    except:
        _log.error("No blog posts found!")
        blog_posts = False
        
    return utilities.clean_response("blogger/index.html",
                                    {'blog_posts': blog_posts,
                                     'extra_style_link': utilities.get_browser_style(request)})



def view_post(request, _identifier):
    """ view a post by identifier.
        identifier can be:
            pk (id)
            slug
            title
    """
    
    post_ = blogtools.get_post_byany(_identifier)
    
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
        
        # no content found.
        if blogtools.get_post_body(post_) == "":
            response = utilities.alert_message("Sorry, no content found for this post.",
                                               "<a href='/blog'><span>Click here to go back to the blog index.</span></a>")
        else:
            # prepare content (do highlighting)
            #post_body = blogtools.prepare_content(post_body)
            
            # Build clean HttpResponse with post template...
            response = utilities.clean_response("blogger/post.html",
                                                {'extra_style_link': utilities.get_browser_style(request),
                                                 'post_title_short': post_title_short,
                                                 'blog_post': post_,
                                                 })
        return response

def view_tags(request):
    """ list all posts by tags (categories) """
    
    return HttpResponse("You are looking for all tags.")


def view_tag(request, _tag):
    """ list all posts with these tags """
    
    
    tag_name = _tag
    blog_posts = blogtools.fix_post_list(blogtools.get_posts_by_tag(tag_name))
    post_count = len(blog_posts)
    
    return utilities.clean_response("blogger/tag.html",
                                    {'extra_style_link': utilities.get_browser_style(request),
                                     'extra_style_link2': "/static/css/tags.css",
                                     'tag_name': tag_name,
                                     'post_count': post_count,
                                     'blog_posts': blog_posts})

def no_identifier(request):
    """ returns a message when user forgets to add an identifier """
    
    return utilities.redirect_response('/blog')


