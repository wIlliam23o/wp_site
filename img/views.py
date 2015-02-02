""" Welborn Productions - img - views
    Handles requests for the img app, returns HttpRequests with proper content.
    -Christopher Welborn 2-2-15
"""

from wp_main.utilities import responses


@responses.staff_required(user_error='You must be logged in to view images.')
def view_index(request):
    return responses.basic_response('Not implemented yet.')


@responses.staff_required(user_error='You must be logged in to upload images.')
def view_upload(request):
    return responses.basic_response('Not implemented yet.')
