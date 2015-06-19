""" Welborn Productions - Blogger - Search
        Provides the functions needed by the searcher app.
"""

from blogger.models import wp_blog
from blogger import blogtools


def get_content(post, request=None):
    """ Return the full body/content for a post. """
    return blogtools.get_post_body(post)


def get_desc(post):
    """ Get description to search and display. """
    return blogtools.get_post_body_short(post, max_text_lines=16)


def get_objects():
    """ Returns searchable objects from the blogger app. """
    return wp_blog.objects.filter(disabled=False).order_by('-posted')


def get_targets(post, content=None, desc=None):
    """ Returns searchable target strings for a blog post. """

    content = content or get_content(post)
    desc = desc or get_desc(post)
    return (
        post.title,
        post.slug,
        content,
        desc,
        str(post.posted)
    )


def result_args(post, desc=None):
    """ Returns the information needed to create a WpResult from
        the searcher app.
        Arguments:
            post  : Post object to gather info from.
            desc  : Optional desc text to display.
                    If not given, the body is formatted to create a desc.
        ex:
            result = WpResult(**format_result_args(post))
    """
    desc = desc or get_desc(post)
    return {
        'title': post.title,
        'desc': desc,
        'link': '/blog/view/{}'.format(post.slug),
        'posted': str(post.posted),
        'restype': 'Blog Post'
    }
