"""
    template tags for welbornproductions blog templates.
    -Christopher Welborn
"""


from django import template
from blogger import blogtools
#from wp_main.utilities import htmltools
from django.utils.safestring import mark_safe
register = template.Library()


@register.filter
def get_body(post):
    """ returns the body to use. see blogtools.get_post_body() """

    return mark_safe(
        blogtools.get_post_body(post))


@register.filter
def get_body_short(post):
    """ returns the body for a listing, shortened if needed. """

    return mark_safe(
        blogtools.get_post_body_short(post))


@register.filter
def get_projects(post):
    """ returns a list of all related projects for a post. """
    try:
        return post.project.all()
    except Exception:
        return []


@register.filter
def tag_links(value):
    """ returns tag list html string for template
        expects wp_blog post, or wp_blog.tags string.
    """

    return mark_safe(blogtools.get_tag_links(value))
