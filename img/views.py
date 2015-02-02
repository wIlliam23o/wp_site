""" Welborn Productions - img - views
    Handles requests for the img app, returns HttpRequests with proper content.
    -Christopher Welborn 2-2-15
"""

from wp_main.utilities import responses


@responses.staff_required(user_error='You must be logged in to view images.')
def view_index(request):
    context = None
    return responses.clean_response("img/index.html", context)
