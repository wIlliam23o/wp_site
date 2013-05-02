#Blog Info/Tools
from blogger.models import wp_blog
from blogger import blogtools

# Global settings (for getting absolute path)
from django.conf import settings

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities.wp_logging import logger
_log = logger("blog").log

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
        
    return responses.clean_response("blogger/index.html",
                                    {'request': request,
                                     'blog_posts': blog_posts,
                                     'post_count': post_count,
                                     'extra_style_link_list': [utilities.get_browser_style(request)]})


def index_page(request):
    """ return a slice of all posts using start_id and max_posts
        to determine the location.
    """
    
    # get overall total of all blog posts
    post_count = wp_blog.objects.count()
    # get request args.
    page_args = responses.get_paged_args(request, post_count)
    # retrieve blog posts slice
    post_slice = blogtools.get_post_list(starting_index=page_args['start_id'],
                                         max_posts=page_args['max_items'],
                                         _order_by=page_args['order_by'])
    # fix posts for listing.
    blog_posts = blogtools.fix_post_list(post_slice, max_text_lines=16)
    # get last index.     
    end_id = str(page_args['start_id'] + len(post_slice))
    return responses.clean_response("blogger/index_paged.html",
                                    {'request': request,
                                     "blog_posts": blog_posts,
                                     "start_id": (page_args['start_id'] + 1),
                                     "end_id": end_id,
                                     "post_count": post_count,
                                     "prev_page": page_args['prev_page'],
                                     "next_page": page_args['next_page'],
                                     "has_prev": (page_args['start_id'] > 0),
                                     "has_next": (page_args['start_id'] < (post_count - page_args['max_items'])),
                                     "extra_style_link_list": [utilities.get_browser_style(request)],
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
        response = responses.alert_message("Sorry, I can't find that post.",
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
            response = responses.alert_message("Sorry, no content found for this post.",
                                               "<a href='/blog'><span>Click here to go back to the blog index.</span></a>")
        else:
            # increment view count
            post_.view_count += 1
            post_.save()
            # enable comments.
            enable_comments = post_.enable_comments
            # Build clean HttpResponse with post template...
            response = responses.clean_response("blogger/post.html",
                                                {'request': request,
                                                 'extra_style_link_list': [utilities.get_browser_style(request)],
                                                 'post_title_short': post_title_short,
                                                 'enable_comments': enable_comments,
                                                 'blog_post': post_,
                                                 })
        return response

def view_tags(request):
    """ list all posts by tags (categories) """
    
    # get all tag counts
    tag_count = blogtools.get_tags_post_count()
    tag_sizes = blogtools.get_tags_fontsizes(tag_count)
    # build list of tags and info for tags.html template
    tag_list = []
    for tag_name in tag_count.keys():
        tag_list.append(blogtools.wp_tag(name_=tag_name,
                                         count_=tag_count[tag_name], 
                                         size_=tag_sizes[tag_name]))
    
    return responses.clean_response("blogger/tags.html",
                                    {'request': request,
                                     'tag_list': tag_list,
                                     'tag_count': len(tag_list),
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     })


def view_tag(request, _tag):
    """ list all posts with these tags """
    
    
    tag_name = utilities.trim_special(_tag).replace(',', ' ')
    found_posts = blogtools.get_posts_by_tag(tag_name, starting_index=0, max_posts=-1)
    post_count = len(found_posts)
    
    blog_posts = blogtools.fix_post_list(found_posts, max_posts=25, max_text_lines=16)
    item_count = len(blog_posts)
    return responses.clean_response("blogger/tag.html",
                                    {'request': request,
                                     'extra_style_link_list': [utilities.get_browser_style(request)],
                                     'tag_name': tag_name,
                                     'post_count': post_count,
                                     'item_count': item_count,
                                     'blog_posts': blog_posts})


def tag_page(request, _tag):
    """ view all posts with this tag, paged. """
    
    # fix tag name
    tag_name = utilities.trim_special(_tag).replace(',', ' ')
    # get all found posts. no slice.
    all_posts = blogtools.get_posts_by_tag(tag_name, starting_index=0, max_posts=-1)

    # overall total of all blog posts with this tag.
    post_count = len(all_posts)
    # get request args.
    page_args = responses.get_paged_args(request, post_count)
    # retrieve blog posts slice
    post_slice = blogtools.get_posts_by_tag(tag_name, 
                                            starting_index=page_args['start_id'],
                                            max_posts=page_args['max_items'],
                                            _order_by=page_args['order_by'])
        
    # fix posts for listing.
    blog_posts = blogtools.fix_post_list(post_slice, max_text_lines=16)
    # number of items in this slice (to get the last index)
    end_id = str(page_args['start_id'] + len(blog_posts))
    # build page.
    return responses.clean_response("blogger/tag_paged.html",
                                    {"request": request,
                                     "blog_posts": blog_posts,
                                     "tag_name": tag_name,
                                     "start_id": (page_args['start_id'] + 1),
                                     "end_id": end_id,
                                     "post_count": post_count,
                                     "prev_page": page_args['prev_page'],
                                     "next_page": page_args['next_page'],
                                     "extra_style_link_list": [utilities.get_browser_style(request)],
                                     "has_prev": (page_args['start_id'] > 0),
                                     "has_next": (page_args['start_id'] < (post_count - page_args['max_items'])),
                                     })    
def no_identifier(request):
    """ returns a message when user forgets to add an identifier """
    
    return responses.redirect_response('/blog')




