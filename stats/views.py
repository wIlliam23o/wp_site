""" Welborn Productions - Stats
    Gathers stats about projects, posts, etc. and displays them.
    Stats tools can also be imported for use with the wpstats command.
"""

from django.contrib.auth.decorators import login_required

from wp_main.utilities import (
    responses,
    utilities,
    wp_logging
)
_log = wp_logging.logger('stats').log


@login_required(login_url='/login')
def view_index(request):
    """ Render the landing page for /stats and show a general
        overview of all the stats.
    """
    context = {
        'request': request,
        'extra_style_link_list': [utilities.get_browser_style(request)]
    }
    return responses.clean_response('stats/index.html', context)
