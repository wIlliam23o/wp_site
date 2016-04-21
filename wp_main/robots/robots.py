#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' Welborn Productions - Robots
    Serves a robots.txt file.
    -Christopher Welborn 4-9-13
'''
from django.views.decorators.cache import never_cache
from wp_main.utilities import responses

disallowed = {
    '/apps/timekeeper/',
}
disallowed_template = """
User-agent: *
{config}
"""

robots_any = """
User-agent: *
Allow: /
""".lstrip()

robots_block = """
User-agent: *
Disallow: /
""".lstrip()


@never_cache
def view_robots_blockall(request):
    """ Block all pages """
    return responses.text_response(robots_block)


@never_cache
def view_robots_any(request):
    """ Allow any page """
    if disallowed:
        # Only allow pages not in disallowed.
        return responses.text_response(
            disallowed_template.format(
                config='\n'.join('Disallow: {}'.format(s) for s in disallowed)
            )
        )
    # Don't block any pages.
    return responses.text_response(robots_any)


@never_cache
def view_byserver(request):
    """ decide which robots.txt to serve up based on current server.
        currently blocks all for any servername starting with 'test.'
    """

    server_name = request.META['SERVER_NAME']

    if server_name.startswith('test.'):
        return view_robots_blockall(request)
    else:
        # normal robots, allow all.
        return view_robots_any(request)
