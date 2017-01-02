#!/usr/bin/env python3
"""
    Helper for ObjectUpdate, that allows this model to be updated/viewed
    from the command line.
    -Christopher Welborn 1-1-17
"""
from blogger.models import wp_blog
# Model to work with.
model = wp_blog
# Name for these models.
name = 'Blog'
# Attributes to use for identifiers when looking up an object.
attrs = ('title', 'slug')


def do_list():
    """ List all blog post titles. """
    try:
        posts = [p for p in wp_blog.objects.order_by('-posted')]
    except Exception as ex:
        raise ValueError('Unable to list blog posts!\n{}'.format(ex))
    if not posts:
        raise ValueError('No posts found!')

    print('Found {} blog posts:'.format(str(len(posts))))
    for post in posts:
        print('    {} ({})'.format(post.title, post.slug))

    return True
