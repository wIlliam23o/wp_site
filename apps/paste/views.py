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
from apps.models import wp_app


_log = logger('apps.paste').log
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache


# Maximum amount of replies to build a vertical menu with.
REPLYMAX = 10
# Maximum amount of pastes to show in simple listings.
LISTINGMAX = 25


def list_view(request, title=None, filterkw=None, orderby=None):
    """ A view that lists posts based on filter() kwargs,
        order_by() kwargs.
    """
    if filterkw is None:
        filterkw = {}
    if title is None:
        title = 'Pastes'
    # Default behaviour is to not show disabled pastes.
    if not 'disabled' in filterkw.keys():
        filterkw['disabled'] = False

    try:
        p = wp_paste.objects.filter(**filterkw)
        if orderby is not None:
            p = p.order_by(orderby)
    except Exception as ex:
        errmsg = 'Unable to retrieve pastes for: {}\n{}'
        _log.error(errmsg.format(title, ex))
        p = []

    if len(p) > LISTINGMAX:
        p = p[:LISTINGMAX]

    context = {
        'request': request,
        'pastes': p,
        'listing_title': title,
    }
    return responses.clean_response('paste/listing.html', context)


def view_api(request):
    """ Landing page for api help. """

    context = {'request': request}
    return responses.clean_response('paste/api.html', context)


@csrf_protect
@ensure_csrf_cookie
def view_index(request):
    """  Main page for pastebin. Add a new paste. """
    # Update the view count for the paste app.
    app = get_object(wp_app.objects, alias='paste')
    if app:
        app.view_count += 1
        app.save()
    
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
def view_json(request):
    """ View a paste, return info in JSON form. """

    def err_data(msg=None):
        """ Build JSON data for an error. """
        errresp = {
            'status': 'error',
            'title': '',
            'author': '',
            'date': '',
            'content': '',
            'id': '',
            'pastes': [],
            'views': 0,
            'count': 0,
            'replies': [],
            'replycount': 0,
            'replyto': '',
            'message': msg if msg else '',
        }
        return errresp

    def paste_data(paste, doreplies=True, doparent=True):
        """ Build JSON data for a paste. """
        resp = {
            'title': paste.title,
            'author': paste.author,
            'date': str(paste.publish_date),
            'content': paste.content,
            'id': paste.paste_id,
            'views': paste.view_count,
        }
        if doreplies:
            replies = paste.children.filter(disabled=False)
            replies = replies.order_by('-publish_date')
            resp['replies'] = [p.paste_id for p in replies]
        else:
            replies = []
        resp['replycount'] = len(replies)

        if doparent:
            if paste.parent:
                resp['replyto'] = paste.parent.paste_id
            else:
                resp['replyto'] = ''
        else:
            resp['replyto'] = ''
        return resp

    try:
        reqargs = request.REQUEST
    except AttributeError:
        reqargs = None
    if not reqargs:
        # No args passed with request, show landing page.
        return view_api(request)

    # Request has args, get paste id.
    pasteidarg = responses.get_request_arg(request, 'id')
    if pasteidarg is None:
        respdata = err_data('No paste id given.')
        return responses.json_response(respdata)

    if pasteidarg.lower() in ('all', 'latest', 'top'):
        # List all paste items (with custom orderby)
        pastes = wp_paste.objects.filter(disabled=False)
        respdata = {'count': 0, 'pastes': []}
        if pasteidarg.lower() == 'top':
            orderby = '-view_count'
        else:
            orderby = '-publish_date'
        # Build pastes data.
        for p in pastes.order_by(orderby):
            respdata['pastes'].append(paste_data(p))
        respdata['count'] = len(respdata['pastes'])
        respdata['status'] = 'ok'
        if respdata['count'] > 0:
            msg = '{} pastes retrieved.'.format(respdata['count'])
        else:
            msg = 'No pastes to retrieve.'
        respdata['message'] = msg
    else:
        # Try getting a single paste object.
        pasteobj = get_object(wp_paste.objects, paste_id=pasteidarg)
        if pasteobj is None:
            # No paste found.
            respdata = err_data('Paste not found: {}'.format(pasteidarg))
            return responses.json_response(respdata)

        # Have paste object, make sure it's not disabled.
        if pasteobj.disabled:
            respdata = err_data('Paste was disabled.')
            return responses.json_response(respdata)
        # Valid paste, build the response data.
        respdata = paste_data(pasteobj)
        respdata['status'] = 'ok'
        respdata['message'] = 'Paste id: {} retrieved.'.format(respdata['id'])

    # Valid paste, send its data in JSON form.
    return responses.json_response(respdata)


@never_cache
@csrf_protect
def view_latest(request):
    """ View latest pastes  """
    return list_view(request, title='Latest Pastes', orderby='-publish_date')


@never_cache
@csrf_protect
def view_paste(request):
    """ View existing paste. """

    pasteidarg = responses.get_request_arg(request, 'id')
    replytoidarg = responses.get_request_arg(request, 'replyto')
    if pasteidarg and replytoidarg:
        # Can't have both.
        return responses.error404(request, 'Invalid url.')

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
            return responses.error404(request, errmsg)
        elif pasteobj.disabled:
            errmsg = 'Paste was disabled: {}'.format(pasteidarg)
            return responses.error404(request, errmsg)
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
            return responses.error404(request, errmsg)
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
        raise responses.error404(request, 'No paste id given.')

    pasteobj = get_object(wp_paste.objects,
                          paste_id=pasteidarg,
                          disabled=False)
    if pasteobj is None:
        # No paste found.
        errmsg = 'Paste not found: {}'.format(pasteidarg)
        raise responses.error404(request, errmsg)

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

    return list_view(request, title='Top Pastes', orderby='-view_count')


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
        raise responses.error404(request, 'Invalid request.')

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
