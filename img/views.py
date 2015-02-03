""" Welborn Productions - img - views
    Handles requests for the img app, returns HttpRequests with proper content.
    -Christopher Welborn 2-2-15
"""

from wp_main.utilities import responses, utilities, wp_logging
from img.models import wp_image

log = wp_logging.logger('img').log

# TODO: Implement a single image view by id. (to include the title and desc.)


def view_index(request):
    """ List all uploaded images, or an album's images (GET /img?album=<name>).
        Present the upload button to staff.
    """
    alert_msg = None
    alert_class = None
    imagefilter = {
        'disabled': False
    }
    album = request.GET.get('album', None)
    if album:
        # Filter by album. TODO: This may need it's own view.
        imagefilter['album'] = album

    if request.user.is_staff:
        if request.FILES:
            # Handle file upload.
            alert_class, alert_msg = handle_files(request)
    else:
        if request.FILES:
            log.error(
                'Non-staff tried to upload files: {}'.format(
                    utilities.get_remote_ip(request)))
        # No private images for the public.
        imagefilter['private'] = False

    images = wp_image.objects.filter(**imagefilter)

    if album and (not images):
        alert_msg = 'No album by that name.'
        alert_class = 'error'
        album = None

    context = {
        'request': request,
        'images': images.order_by('-publish_date'),
        'album': album,
        'extra_style_link_list': [utilities.get_browser_style(request)],
        'alert_message': alert_msg,
        'alert_class': alert_class
    }
    return responses.clean_response_req(
        template_name='img/index.html',
        context=context,
        request=request)


def handle_files(request):
    """ Handle an uploaded file.
        Returns (alert_class, alert_message) that can be passed to the
        template.
        Errors are logged.
    """
    for f in request.FILES.values():
        log.debug('Uploading file: {}'.format(f.name))
        try:
            newimage = wp_image(
                image=f,
                title=request.REQUEST.get('title', ''),
                description=request.REQUEST.get('description', ''),
                album=request.REQUEST.get('album', ''),
                private=request.REQUEST.get('private', False)
            )
            newimage.save()
        except Exception as ex:
            log.error('Error uploading an image: {}\n{}'.format(f.name, ex))
            return 'error', 'There was an error while uploading your image.'

    # Success.
    return 'approved', 'Your image was uploaded.'
