from django.http import HttpResponse
#from django.template import Context, loader
#from django.utils.safestring import mark_safe # don't escape html with strings marked safe.


from blogger.models import wp_blog
from blogger import blogtools

# Global settings (for getting absolute path)
from django.conf import settings
# logging capabilities
from wp_main.wp_logging import logger
_log = logger("welbornprod.blog", use_file=(not settings.DEBUG))

# welborn productions utilities
from wp_main import utilities

def index(request):
    """ index list of all blog posts """

    # load blog posts...
    try:
        raw_posts = wp_blog.objects.order_by('-posted')
        post_count = len(raw_posts)
        blog_posts = blogtools.fix_post_list(raw_posts,
                                             max_posts=25,
                                             max_text_lines=16)
    except:
        _log.error("No blog posts found!")
        blog_posts = False
        
    return utilities.clean_response("blogger/index.html",
                                    {'blog_posts': blog_posts,
                                     'post_count': post_count,
                                     'extra_style_link': utilities.get_browser_style(request)})


def index_page(request):
    """ return a slice of all posts using start_id and max_posts
        to determine the location.
    """
    
    # get order_by
    order_by_ = utilities.get_request_arg(request, 'order_by', '-posted')
        
    # get max_posts
    max_posts_ = utilities.get_request_arg(request, 'max_posts', 25, min_val=1, max_val=100)
    # calculate last page based on max_posts
    post_count = wp_blog.objects.count()   
    last_page = ( post_count - max_posts_ ) if ( post_count > max_posts_ ) else 0

    # get start_id
    start_id = utilities.get_request_arg(request, 'start_id', 0, min_val=0, max_val=9999)
    # fix starting id.
    if isinstance(start_id, (str, unicode)):
        if start_id.lower() == 'last':
            start_id = last_page
        else:
            # this shouldn't happen, get_request_arg() returns an integer or float
            # if a good integer/float value was passed. So any unexpected string value
            # means someone is messing with the args in a way that would break the view.
            # so if the conditions above aren't met ('last'), it defaults to a safe value (0).
            start_id = 0
        
    # fix maximum start_id
    if start_id > last_page:
        start_id = last_page
        
    # get prev page
    prev_page = start_id - max_posts_
    if prev_page < 0:
        prev_page = 0
    # get next page
    next_page = start_id + max_posts_
    if next_page > wp_blog.objects.count():
        next_page = last_page
    
    # retrieve blog posts slice
    post_slice = blogtools.get_post_list(start_id,
                                         max_posts=max_posts_,
                                         _order_by=order_by_)
    blog_posts = blogtools.fix_post_list(post_slice, max_text_lines=16)        
    # fix nav info
    end_id = str(start_id + len(blog_posts))

    return utilities.clean_response("blogger/index_paged.html",
                                    {"blog_posts": blog_posts,
                                     "start_id": (start_id + 1),
                                     "end_id": end_id,
                                     "post_count": post_count,
                                     "prev_page": prev_page,
                                     "next_page": next_page,
                                    "extra_style_link": utilities.get_browser_style(request),
                                    })

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
            # increment view count
            post_.view_count += 1
            # enable comments.
            enable_comments = post_.enable_comments
            # Build clean HttpResponse with post template...
            response = utilities.clean_response("blogger/post.html",
                                                {'extra_style_link': utilities.get_browser_style(request),
                                                 'post_title_short': post_title_short,
                                                 'enable_comments': enable_comments,
                                                 'blog_post': post_,
                                                 })
        return response

def view_tags(request):
    """ list all posts by tags (categories) """
    
    return HttpResponse("You are looking for all tags.")


def view_tag(request, _tag):
    """ list all posts with these tags """
    
    
    tag_name = utilities.trim_special(_tag).replace(',', ' ')
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


