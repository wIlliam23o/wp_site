"""
    Welborn Productions - Apps - Paste - Views
        Provides template-rendering and request-handling for the pastebin app.
    -Christopher Welborn 2014
"""

from wp_main.utilities import responses
from wp_main.utilities.wp_logging import logger
from wp_main.utilities.utilities import get_object, get_remote_ip

# For creating/accessing wp_paste() objects.
from apps.paste.models import wp_paste


_log = logger('apps.paste').log
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache


# Maximum amount of replies to build a vertical menu with.
REPLYMAX = 10
# Maximum amount of pastes to show in simple listings.
LISTINGMAX = 25

# TODO: Add 'view all pastes', 'view all replies'.


@csrf_protect
@ensure_csrf_cookie
def view_index(request):
    """  Main page for pastebin. Add a new paste. """

    # If the request has args pass it on down to view_paste()
    try:
        reqargs = request.REQUEST
    except AttributeError:
        reqargs = None
    finally:
        if reqargs:
            return view_paste(request)

    # New Paste.
    context = {
        'request': request,
        'paste': None,
        'replyto': None,
        'replies': None,
        'replycount': None,
        'replymax': REPLYMAX,
    }
    return responses.clean_response('paste/index.html', context)


@never_cache
@csrf_protect
def view_latest(request):
    """ View latest pastes  """

    try:
        p = wp_paste.objects.filter(disabled=False).order_by('-publish_date')
    except Exception as ex:
        _log.error('Unable to retrieve pastes:\n{}'.format(ex))
        p = []

    if len(p) > LISTINGMAX:
        p = p[:LISTINGMAX]

    context = {
        'request': request,
        'pastes': p,
        'listing_title': 'Latest Pastes',
    }
    return responses.clean_response('paste/listing.html', context)


@never_cache
@csrf_protect
def view_paste(request):
    """ View existing paste. """

    pasteidarg = responses.get_request_arg(request, 'id')
    replytoidarg = responses.get_request_arg(request, 'replyto')
    if pasteidarg and replytoidarg:
        # Can't have both.
        return responses.error_response(request, 'Invalid url.')

    # These are all optional, the template decides what to show,
    # based on what is available.
    pasteobj = None
    replytoobj = None
    replylast = None
    replies = None
    replycount = None

    if pasteidarg is not None:
        # Lookup existing paste by id.
        pasteobj = get_object(wp_paste.objects,
                              paste_id=pasteidarg)
        if pasteobj is None:
            # Return a 404, that paste cannot be found.
            errmsg = 'Paste not found: {}'.format(pasteidarg)
            return responses.error_response(request, errmsg)
        elif pasteobj.disabled:
            errmsg = 'Paste was disabled: {}'.format(pasteidarg)
            return responses.error_response(request, errmsg)
        else:
            # Grab parent as the replyto object.
            replytoobj = pasteobj.parent
            # Update some info about the paste.
            pasteobj.view_count += 1
            # Save changes.
            pasteobj.save()

    if replytoidarg is not None:
        # Lookup parent paste by id.
        replytoobj = get_object(wp_paste.objects,
                                paste_id=replytoidarg)
        if replytoobj is None:
            # Return a 404, user is trying to reply to a dead paste.
            errmsg = 'Paste not found: {}'.format(replytoidarg)
            return responses.error_response(request, errmsg)
        elif replytoobj.disabled:
            errmsg = 'Paste was disabled: {}'.format(replytoidarg)
            return responses.error_response(request, errmsg)
    # If this paste has a parent, get it and use it as the replyto.
    if pasteobj is not None:
        if pasteobj.parent is not None:
            replytoobj = pasteobj.parent
        # Get all replies for this paste.
        replies = pasteobj.children.order_by('-publish_date')
        if replies:
            # Grab latest reply to this paste.
            replylast = replies[0]
            # Trim replies if they are too long to fit on the page.
            replycount = len(replies)
            replies = replies[:REPLYMAX]

    context = {
        'request': request,
        'paste': pasteobj,
        'replyto': replytoobj,
        'replylast': replylast,
        'replies': replies,
        'replycount': replycount,
        'replymax': REPLYMAX,
    }
    return responses.clean_response('paste/index.html', context)


@never_cache
@csrf_protect
def view_replies(request):
    """ View all replies for a paste. """
    pasteidarg = responses.get_request_arg(request, 'id')
    if pasteidarg is None:
        raise responses.error_response(request, 'No paste id given.')

    pasteobj = get_object(wp_paste.objects,
                          paste_id=pasteidarg,
                          disabled=False)
    if pasteobj is None:
        # No paste found.
        errmsg = 'Paste not found: {}'.format(pasteidarg)
        raise responses.error_response(request, errmsg)

    replies = pasteobj.children.order_by('-publish_date')
    context = {
        'request': request,
        'paste': pasteobj,
        'replies': replies,
    }

    return responses.clean_response('paste/replies.html', context)


@never_cache
@csrf_protect
def view_top(request):
    """ View top pastes (highest view count) """

    try:
        p = wp_paste.objects.filter(disabled=False).order_by('-view_count')
    except Exception as ex:
        _log.error('Unable to retrieve pastes:\n{}'.format(ex))
        p = []

    if len(p) > LISTINGMAX:
        p = p[:LISTINGMAX]

    context = {
        'request': request,
        'pastes': p,
        'listing_title': 'Top Pastes',
    }
    return responses.clean_response('paste/listing.html', context)


@csrf_protect
@ensure_csrf_cookie
def ajax_submit(request):
    """ Handles ajax paste submits.
        Reads json data from request and handles accordingly.
    """
    # Submits should always be ajax/POST.
    if not request.is_ajax():
        remoteip = get_remote_ip()
        if not remoteip:
            remoteip = '<Unknown IP>'
        _log.error('Received non-ajax request from: {}'.format(remoteip))
        raise responses.error_response(request, 'Invalid request.')

    # Get data being submitted.
    submitdata = responses.json_get_request(request)
    #_log.debug('Received submit data:\n{!r}'.format(submitdata))
    if (not submitdata) or (not submitdata.get('content', False)):
        # No valid submit data.
        exc = Exception('Invalid data submitted.')
        return responses.json_response_err(exc)

    # Build a new paste object, strip newlines.
    pastecontent = submitdata.get('content', '').strip()
    if not pastecontent:
        # Invalid content.
        exc = Exception('Empty pastes not allowed.')
        return responses.json_response_err(exc)

    # See if this is a reply.
    replytoid = submitdata.get('replyto', None)
    replytoobj = None
    if replytoid:
        replytoobj = get_object(wp_paste.objects,
                                paste_id=replytoid)
        if replytoobj is None:
            # Trying to reply to a dead paste.
            exc = Exception('No paste with that id: {}'.format(replytoid))
            return responses.json_response_err(exc)
        else:
            # Check for disabled replyto paste.
            if replytoobj.disabled:
                exc = Exception('Paste is disabled: {}'.format(replytoid))
                return responses.json_response_err(exc)

    newpaste = wp_paste(author=submitdata.get('author', ''),
                        title=submitdata.get('title', ''),
                        content=pastecontent,
                        onhold=submitdata.get('onhold', False),
                        language=submitdata.get('language', ''),
                        parent=replytoobj,
                        )

    try:
        # Try saving the new paste.
        newpaste.save()
        # Build success message with id/url/message.
        jsonresp = {
            'status': 'ok',
            'message': 'Paste was a success.',
            'id': newpaste.paste_id,
            'url': newpaste.get_url(),
            'parent': getattr(newpaste.parent, 'paste_id', None),
        }
    except Exception as ex:
        _log.error('Error saving new paste:\n{}'.format(ex))
        return responses.json_response_err(ex)

    # Send JSON response back.
    return responses.json_response(jsonresp)
