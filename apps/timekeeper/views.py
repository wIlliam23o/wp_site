""" WelbornProd - Apps - TimeKeeper - views
    Provides views/responses for the TimeKeeper app.
    -Christopher Welborn 1-11-16
"""
# authorization
from django.contrib.auth.decorators import login_required

# disable cache for ip/useragent pages.
from django.views.decorators.cache import never_cache

# various welbornprod tools
from wp_main.utilities import (
    responses,
)
from apps.timekeeper import tools


@login_required
@never_cache
def view_index(request):
    """ Landing page for the timekeeper app. """
    return responses.clean_response(
        template_name='timekeeper/index.html',
        context={'jobsessions': tools.get_week_jobs()},
        request=request
    )
