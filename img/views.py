""" Welborn Productions - img - views
    Handles requests for the img app, returns HttpRequests with proper content.
    -Christopher Welborn 2-2-15
"""

import logging
log = logging.getLogger('wp.img')

from wp_main.utilities import responses, utilities
from img.models import wp_image


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
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                album=request.POST.get('album', ''),
                private=request.POST.get('private', False)
            )
            newimage.save()
        except Exception as ex:
            log.error('Error uploading an image: {}\n{}'.format(f.name, ex))
            return 'error', 'There was an error while uploading your image.'

    # Success.
    return 'approved', 'Your image was uploaded.'


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
        if album == 'none':
            # Grab all image without an album set.
            album = ''
        if album == 'all':
            # Grab all images.
            album = None
        else:
            # Filter on user-specified album.
            imagefilter['album'] = album
    else:
        # View a single image by id. TODO: Needs it's own url pattern.
        imageid = request.GET.get('id', None)
        if imageid:
            return view_image_id(request, imageid)

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

    if images:
        images = images.order_by('-publish_date')
        # Allow user sort by album.
        if request.GET.get('sort', None) == 'album':
            images = images.order_by('album')

    context = {
        'images': images,
        'album': album,
        'alert_message': alert_msg,
        'alert_class': alert_class
    }
    return responses.clean_response(
        template_name='img/index.html',
        context=context,
        request=request)


def view_image_id(request, imageid):
    """ View a single image by id. """

    images = wp_image.objects.filter(disabled=False, image_id=imageid)
    if not images:
        return responses.error404(
            request,
            ['I can\'t find an image with that id.']
        )

    image = images[0]
    alert_msg, alert_class = None, None
    image.view_count += 1
    image.save()
    log.debug('Image view_count incremented to {}: {}'.format(
        image.view_count,
        image.filename))
    # Reusing part of the index view template.
    # Needs to be more refined, in it's own template.
    context = {
        'image': image,
        'images': (image,),
        'album': None,
        'alert_message': alert_msg,
        'alert_class': alert_class
    }
    return responses.clean_response(
        template_name='img/image.html',
        context=context,
        request=request)
