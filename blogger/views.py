import logging
# Blog Info/Tools
from blogger.models import wp_blog
from blogger import blogtools

# Global settings (for getting absolute path)
# from django.conf import settings  # @UnusedImport: settings

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
log = logging.getLogger('wp.blog')


def index(request):
    """ index list of all blog posts """

    # load blog posts...
    try:
        raw_posts = wp_blog.objects.order_by('-posted_datetime')
        post_count = len(raw_posts)
        blog_posts = blogtools.fix_post_list(raw_posts)
    except Exception as ex:
        log.error("Error getting blog posts!:\n" + str(ex))
        blog_posts = False
        post_count = 0

    context = {
        'request': request,
        'blog_posts': blog_posts,
        'post_count': post_count,
    }
    return responses.clean_response('blogger/index.html', context)


def index_page(request):
    """ return a slice of all posts using start_id and max_posts
        to determine the location.
    """

    # get overall total of all blog posts
    post_count = wp_blog.objects.count()
    # get request args.
    page_args = responses.get_paged_args(request, post_count)
    # Setup defaults incase of missing items/errors.
    startid = page_args.get('start_id', 0)
    maxposts = page_args.get('max_items', blogtools.DEFAULT_MAXPOSTS),
    orderby = page_args.get('order_by', None)
    prevpage = page_args.get('prev_page', None)
    nextpage = page_args.get('next_page', None)
    # retrieve blog posts slice
    try:
        sliceargs = {
            'starting_index': startid,
            'max_posts': maxposts,
            'order_by': orderby,
        }
        post_slice = blogtools.get_post_list(**sliceargs)
        # fix posts for listing.
        blog_posts = blogtools.fix_post_list(post_slice)
    except Exception as ex:
        log.debug('Error getting blog posts slice:\n{}'.format(ex))
        blog_posts = post_slice = end_id = False

    # get last index, 'has next page', and 'has prev page'
    end_id = startid + len(post_slice)
    hasnxt = startid < (post_count - maxposts)
    hasprv = startid > 0

    # Template values.
    context = {
        'request': request,
        'blog_posts': blog_posts,
        'start_id': (startid + 1),
        'end_id': end_id,
        'post_count': post_count,
        'prev_page': prevpage,
        'next_page': nextpage,
        'has_prev': hasprv,
        'has_next': hasnxt,
    }
    return responses.clean_response('blogger/index_paged.html', context)


def view_post(request, identifier):
    """ view a post by identifier.
        identifier can be:
            pk (id)
            slug
            title
    """

    post = blogtools.get_post_byany(identifier)

    if post is None:
        log.error('Post not found: {}'.format(identifier))
        errmsg = 'Sorry, I can\'t find that post.'
        errlink = '\n'.join([
            '<a href=\'/blog\'><span>',
            'Click here to go back to the main blog page.',
            '</span></a>'])

        return responses.alert_message(request, errmsg, body_message=errlink)

    # build blog post.

    # get short title for window-text
    if len(post.title) > 20:
        post_title_short = '..{}'.format(post.title[len(post.title) - 30:])
    else:
        post_title_short = post.title

    # no content found.
    if not blogtools.get_post_body(post):
        errmsg = 'Sorry, no content found for this post.'
        errlink = '\n'.join([
            '<a href=\'/blog\'><span>',
            'Click here to go back to the main blog page.',
            '</span></a>'])
        return responses.alert_message(request, errmsg, body_message=errlink)

    # increment view count
    try:
        post.view_count += 1
        post.save()
    except Exception as exsave:
        log.error('Unable to increment view_count for: '
                  '{}\n{}'.format(post, exsave))

    # Build clean HttpResponse with post template...
    context = {
        'request': request,
        'post_title_short': post_title_short,
        'enable_comments': post.enable_comments,
        'blog_post': post,
        'related_projects': post.get_projects(),
    }
    return responses.clean_response('blogger/post.html', context)


def view_tags(request):
    """ list all posts by tags (categories) """

    # get all tag counts
    tag_count = blogtools.get_tags_post_count()
    tag_sizes = blogtools.get_tags_fontsizes(tag_count)

    def make_tag(tagname):
        """ Make a WpTag() based on count and size info gathered. """
        return blogtools.WpTag(name=tagname,
                               count=tag_count[tagname],
                               size=tag_sizes[tagname])

    # build list of tags and info for tags.html template
    tag_list = [make_tag(tname) for tname in tag_count]
    context = {
        'request': request,
        'tag_list': tag_list,
        'tag_count': len(tag_list),
    }
    return responses.clean_response('blogger/tags.html', context)


def view_tag(request, tag):
    """ list all posts with these tags """

    tag_name = utilities.trim_special(tag).replace(',', ' ')
    found_posts = blogtools.get_posts_by_tag(tag_name,
                                             starting_index=0,
                                             max_posts=-1)
    post_count = len(found_posts)
    # Fix the list (shorten the body, trim to maxposts if needed)
    found_posts = blogtools.fix_post_list(found_posts)

    context = {
        'request': request,
        'tag_name': tag_name,
        'post_count': post_count,
        'item_count': len(found_posts),
        'blog_posts': found_posts
    }
    return responses.clean_response('blogger/tag.html', context)


def tag_page(request, tag):
    """ view all posts with this tag, paged. """

    # fix tag name
    tag_name = utilities.trim_special(tag).replace(',', ' ')
    # get all found posts. no slice.
    all_posts = blogtools.get_posts_by_tag(tag_name, starting_index=0)

    # overall total of all blog posts with this tag.
    post_count = len(all_posts)
    # get request args.
    page_args = responses.get_paged_args(request, post_count)
    startid = page_args.get('start_id', 0)
    maxitems = page_args.get('max_items', None)
    orderby = page_args.get('order_by', None)
    prevpage = page_args.get('prev_page', None)
    nextpage = page_args.get('next_page', None)
    # retrieve blog posts slice
    post_slice = blogtools.get_posts_by_tag(tag_name,
                                            starting_index=startid,
                                            max_posts=maxitems,
                                            order_by=orderby)

    # fix posts for listing.
    blog_posts = blogtools.fix_post_list(post_slice)
    # number of items in this slice (to get the last index)
    end_id = startid + len(blog_posts)
    hasprv = startid > 0
    hasnxt = startid < (post_count < maxitems)
    # build page.
    context = {
        'request': request,
        'blog_posts': blog_posts,
        'tag_name': tag_name,
        'start_id': (startid + 1),
        'end_id': end_id,
        'post_count': post_count,
        'prev_page': prevpage,
        'next_page': nextpage,
        'has_prev': hasprv,
        'has_next': hasnxt,
    }
    return responses.clean_response('blogger/tag_paged.html', context)


def no_identifier(request):
    """ Redirects when user forgets to add an identifier """

    return responses.redirect_response('/blog')
