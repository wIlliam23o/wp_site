""" Welborn Productions - Stats
    Gathers stats about projects, posts, etc. and displays them.
    Stats tools can also be imported for use with the wpstats command.
"""
import logging

from django.contrib.auth.decorators import login_required

from apps.models import wp_app
from apps.paste.models import wp_paste
from blogger.models import wp_blog
from downloads.models import file_tracker
from img.models import wp_image
from misc.models import wp_misc
from projects.models import wp_project

from stats import tools
from wp_main.utilities import (
    responses,
    utilities
)
log = logging.getLogger('wp.stats')


@login_required(login_url='/login')
def view_index(request):
    """ Render the landing page for /stats and show a general
        overview of all the stats.
    """
    if not request.user.is_authenticated():
        # Not authenticated, return the bad login page. No stats for you!
        context = {
            'request': request,
            'extra_style_link_list': [utilities.get_browser_style(request)],
        }
        return responses.clean_response('home/badlogin.html', context)

    # Build the stats page for all known models.
    modelinf = {
        file_tracker: {'orderby': '-download_count'},
        wp_app: {'orderby': '-view_count'},
        wp_blog: {'orderby': '-view_count'},
        wp_image: {
            'orderby': '-view_count',
            'displayattr': ('image_id', 'title', 'image.name'),
            'displayattrsep': ' - '
        },
        wp_misc: {'orderby': '-download_count'},
        wp_paste: {
            'orderby': '-view_count',
            'displayattr': ('paste_id', 'title'),
            'displayattrsep': ' - '
        },
        wp_project: {'orderby': '-download_count'}
    }
    context = {
        'request': request,
        'label': 'all models',
        'stats': tools.get_models_info(modelinf),
        'extra_style_link_list': [utilities.get_browser_style(request)]
    }
    return responses.clean_response('stats/index.html', context)
