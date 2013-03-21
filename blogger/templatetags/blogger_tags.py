""" 
    template tags for welbornproductions blog templates. 
    -Christopher Welborn
"""


from django import template
from blogger import blogtools
from django.utils.safestring import mark_safe
register = template.Library()


def tag_links(value):
    """ returns tag list html string for template 
        expects wp_blog post, or wp_blog.tags string.
    """
    
    return mark_safe(blogtools.get_tag_links(value))


def get_body(value):
    """ returns the body to use. see blogtools.get_post_body() """
    
    return mark_safe(blogtools.prepare_content(blogtools.get_post_body(value)))


register.filter('tag_links', tag_links)
register.filter('get_body', get_body)