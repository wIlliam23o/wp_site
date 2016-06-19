"""
    Welborn Productions - Apps - Paste - Views
        Provides template-rendering and request-handling for the pastebin app.
    -Christopher Welborn 2014
"""

import logging
from datetime import datetime

from django.views.decorators.csrf import (
    csrf_protect, ensure_csrf_cookie, csrf_exempt
)
from django.views.decorators.cache import never_cache

from wp_main.utilities import responses
from wp_main.utilities.utilities import (
    get_object, get_remote_ip, parse_bool
)

# For creating/accessing wp_paste() objects.
from apps.paste.models import wp_paste
from apps.models import wp_app


# Log object for logging.
log = logging.getLogger('wp.apps.paste')
# Maximum amount of replies to build a vertical menu with.
REPLYMAX = 10
# Maximum amount of pastes to show in simple listings.
LISTINGMAX = 25
# Minimum seconds allowed between public api paste submits.
MIN_SUBMIT_SECS = 15


def invalidate_submit(submitdata):
    """ Validate an author/user's ip address.
        Do not allow fast, multiple, duplicate, pastes.
        Returns None (Falsey) if the ip is okay, otherwise a string
        containing the reason the paste failed (Truthy).
        Example:
            invalid_reason = invalidate_submit({
                'author_ip': '127.0.0.1',
                'content': 'Test',
                'publish_date': datetime.today()})
            if invalid_reason:
                reject_the_paste('Not allowed: {}'.format(invalid_reason))
            else:
                save_the_paste()

        Arguments:
            submitdata  : A dict of paste data, usually from JSON.
    """

    ipaddr = submitdata.get('author_ip', None)
    if not ipaddr:
        # None, or '' was passed (unable to get ip,  give'em a break)
        return None

    userpastes = wp_paste.objects.filter(author_ip=ipaddr)
    if not userpastes:
        # User has no pastes..
        return None

    # Get user's last paste.
    lastpaste = userpastes.latest('publish_date')
    try:
        elapsed = (datetime.now() - lastpaste.publish_date).total_seconds()
    except Exception as ex:
        log.error('Error getting elapsed paste-time for: {}\n{}'.format(
            lastpaste,
            ex))
        # Don't fault a possibly good user for our error.
        return None

    # Deny pastes that are less than MIN_SUBMIT_SECS (seconds) apart.
    if elapsed < MIN_SUBMIT_SECS:
        return 'Last paste time: {}s ago'.format(elapsed)

    # Deny pastes that have the same content as the last one.
    content = submitdata.get('content', None)
    if not content:
        return 'Paste has no content.'

    lang = submitdata.get('language', None)
    if (content == lastpaste.content) and (lang == lastpaste.language):
        return 'Same as last paste.'

    # Paste passed the gauntlet.
    return None


def json_paste(request, pasteidarg):
    """ Get a single paste in JSON format.
        Returns an HttpResponse with application/json.
    """
    # Try getting a single paste object.
    pasteobj = get_object(wp_paste.objects, paste_id=pasteidarg)
    if pasteobj is None:
        # No paste found.
        respdata = paste_err_data('Paste not found: {}'.format(pasteidarg))
        return responses.json_response(respdata)

    # Have paste object, make sure it's not disabled.
    if pasteobj.disabled:
        respdata = paste_err_data('Paste is disabled.')
        return responses.json_response(respdata)
    elif (not request.user.is_staff) and pasteobj.is_expired():
        respdata = paste_err_data('Paste is expired.')
        return responses.json_response(respdata)

    # Valid paste, build the response data.
    respdata = paste_data(pasteobj)
    respdata['status'] = 'ok'
    respdata['message'] = 'Paste id: {} retrieved.'.format(respdata['id'])

    return responses.json_response(respdata)


def json_paste_listing(groupby=None):
    """ Get a paste listing in JSON format.
        Returns an HttpResponse with application/json.
        Arguments:
            groupby  : None, 'all', 'latest': Sort by date.
                       'top' : Sort by view count.
    """
    # List all paste items (with custom orderby)
    pastes = wp_paste.objects.filter(disabled=False, private=False)
    respdata = {'count': 0, 'pastes': []}
    if groupby == 'top':
        orderby = '-view_count'
    else:
        orderby = '-publish_date'

    # Build pastes data. Only public and unexpired pastes should show.
    respdata['pastes'] = [
        paste_data(p) for p in pastes.order_by(orderby)
        if not p.is_expired()
    ]
    respdata['count'] = len(respdata['pastes'])
    respdata['status'] = 'ok'
    if respdata['count'] == 0:
        respdata['message'] = 'No pastes to retrieve.'
    else:
        respdata['message'] = (
            '{} pastes retrieved.'.format(respdata['count']))
    return responses.json_response(respdata)


def list_view(request, title=None, filterkw=None, orderby=None):
    """ A view that lists posts based on filter() kwargs,
        order_by() kwargs.
    """
    if filterkw is None:
        filterkw = {}
    if title is None:
        title = 'Pastes'
    # Default behaviour is to not show disabled/private pastes.
    if 'disabled' not in filterkw:
        filterkw['disabled'] = False
    # Private pastes are only viewable directly, not in listings.
    if 'private' not in filterkw:
        filterkw['private'] = False

    try:
        p = wp_paste.objects.filter(**filterkw)
        if orderby is not None:
            p = p.order_by(orderby)
        # Expired pastes should not show up in the list for non-admins.
        if not request.user.is_staff:
            p = [paste for paste in p if not paste.is_expired()]
    except Exception as ex:
        errmsg = 'Unable to retrieve pastes for: {}\n{}'
        log.error(errmsg.format(title, ex))
        p = []

    if len(p) > LISTINGMAX:
        p = p[:LISTINGMAX]

    context = {
        'pastes': p,
        'listing_title': title,
    }
    return responses.clean_response(
        'paste/listing.html',
        context=context,
        request=request)


def paste_err_data(msg=None):
    """ Build Paste JSON data for an error. """
    return {
        'status': 'error',
        'title': '',
        'author': '',
        'date': '',
        'content': '',
        'language': '',
        'id': '',
        'pastes': [],
        'views': 0,
        'count': 0,
        'replies': [],
        'replycount': 0,
        'replyto': '',
        'message': msg if msg else '',
    }


def paste_data(paste, doreplies=True, doparent=True):
    """ Build Paste JSON data for a valid paste. """
    resp = {
        'title': paste.title,
        'author': paste.author,
        'date': str(paste.publish_date),
        'content': paste.content,
        'id': paste.paste_id,
        'views': paste.view_count,
        'language': paste.language,
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


def process_submit(submitdata, apisubmit=False):
    """ Given request arguments, parses them and tries to create a new paste.
        The submitdata can be any dict.
        ...usually comes from responses.json_get_request(request)

        Arguments:
            submitdata  : Data/dict to be fill paste info.
            apisubmit   : Whether this was a public-api submit.
                          Default: False

        Responses are in JSON..
        Returns:
          HttpResponse(responsedata, content_type='application/json')
    """

    if (not submitdata) or (not submitdata.get('content', False)):
        # No valid submit data.
        exc = ValueError('Invalid data submitted.')
        return responses.json_response_err(exc)

    # Build a new paste object, strip newlines.
    pastecontent = submitdata.get('content', '').strip()
    if not pastecontent:
        # Invalid content.
        exc = ValueError('Empty pastes not allowed.')
        return responses.json_response_err(exc)

    # See if this is a reply.
    replytoid = submitdata.get('replyto', None)
    replytoobj = None
    if replytoid:
        replytoobj = get_object(
            wp_paste.objects,
            paste_id=replytoid
        )
        if replytoobj is None:
            # Trying to reply to a dead paste.
            errmsg = 'No paste with that id: {}'.format(replytoid)
            exc = ValueError(errmsg)
            log.debug(errmsg)
            return responses.json_response_err(exc)
        else:
            # Check for disabled replyto paste.
            if replytoobj.disabled:
                errmsg = 'Paste is disabled or expired: {}'.format(replytoid)
                exc = ValueError(errmsg)
                log.debug(errmsg)
                return responses.json_response_err(exc)

    newpaste = wp_paste(
        author=submitdata.get('author', ''),
        author_ip=submitdata.get('author_ip', ''),
        title=submitdata.get('title', ''),
        content=pastecontent,
        onhold=submitdata.get('onhold', False),
        language=submitdata.get('language', ''),
        parent=replytoobj,
        private=submitdata.get('private', False),
        apisubmit=apisubmit,
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
        log.error('Error saving new paste:\n{}'.format(ex))
        return responses.json_response_err(ex)

    # Send JSON response back.
    return responses.json_response(jsonresp)


@csrf_protect
@ensure_csrf_cookie
def submit_ajax(request):
    """ Handles ajax paste submits.
        Reads json data from request and handles accordingly.
        These requests must come from the welbornprod site.
    """
    # Submits should always be ajax/POST.
    if not request.is_ajax():
        remoteip = get_remote_ip(request)
        if not remoteip:
            remoteip = '<Unknown IP>'
        log.error('Received non-ajax request from: {}'.format(remoteip))
        return responses.error500(
            request,
            msgs=('Invalid request.', ),
            user_error=' '.join((
                'Try entering a valid url,',
                'or using the forms/buttons provided.',
                '-Cj'
            ))
        )

    # Get the request args for this submit (JSON only).
    submitdata = responses.json_get_request(request)
    if (not submitdata) or (not submitdata.get('content', False)):
        # No valid submit data.
        exc = ValueError('Invalid data submitted.')
        return responses.json_response_err(exc)

    # Add the user's ip address to the paste data.
    submitdata['author_ip'] = get_remote_ip(request)

    # Try building a paste, and return a JSON response.
    return process_submit(submitdata)


@csrf_exempt
def submit_public(request):
    """ A public paste submission
        (may have to pass a gauntlet of checks)
    """

    # Get the request args for this submit.
    submitdata = responses.json_get_request(request, suppress_errors=True)
    # Try using GET/POST..
    if not submitdata:
        submitdata = responses.get_request_args(request)
        # Using multiple content args, but first for the rest.
        submitdata['content'] = '\n'.join(submitdata.getlist('content', []))
        # Parse a few args that string values would break.
        onhold = parse_bool(submitdata.get('onhold', ''))
        private = parse_bool(submitdata.get('private', ''))
        submitdata.update({'onhold': onhold, 'private': private})

    if (not submitdata) or (not submitdata.get('content', False)):
        # No valid submit data.
        exc = ValueError('Invalid data submitted.')
        return responses.json_response_err(exc)

    # Add author's ip to the paste info.
    submitdata['author_ip'] = get_remote_ip(request)

    invalidsubmit = invalidate_submit(submitdata)
    if invalidsubmit:
        # User is not allowed to paste again right now.
        log.debug('User paste invalidated: '
                  '{} - {}'.format(submitdata['author_ip'], invalidsubmit))
        err = ValueError(invalidsubmit)
        return responses.json_response_err(err)

    # Try building a paste, and return JSON response.
    return process_submit(submitdata, apisubmit=True)


def view_api(request):
    """ Landing page for api help. """
    return responses.clean_response(
        'paste/api.html',
        context=None,
        request=request)


@csrf_protect
@ensure_csrf_cookie
def view_index(request):
    """ Main page for pastebin. Add a new paste.
        Arguments:
            request        : Django's Request object.
            template_name  : Template to render.
    """
    # Update the view count for the paste app.
    app = get_object(wp_app.objects, alias='paste')
    if app:
        app.view_count += 1
        app.save()

    # If the request has args pass it on down to view_paste()
    if request.GET or request.POST:
        return view_paste(request)

    # New Paste.
    context = {
        'paste': None,
        'replyto': None,
        'replies': None,
        'replycount': None,
        'replymax': REPLYMAX,
    }
    return responses.clean_response(
        'paste/index.html',
        context=context,
        request=request)


@never_cache
def view_json(request):
    """ View a paste, return info in JSON form. """

    reqargs = request.POST or request.GET
    if not reqargs:
        # No args passed with request, show landing page.
        return view_api(request)

    # Request has args, get paste id.
    pasteidarg = responses.get_request_arg(request, 'id')
    if pasteidarg is None:
        respdata = paste_err_data('No paste id given.')
        return responses.json_response(respdata)
    else:
        pasteidarg = pasteidarg.lower()

    if pasteidarg in {'all', 'latest', 'top'}:
        # Paste listing.
        return json_paste_listing(pasteidarg)

    # Try retrieving a single paste.
    return json_paste(request, pasteidarg)


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
        # Can't have both id and replyto.
        return responses.error404(request, 'Invalid url.')

    # These are all optional, the template decides what to show,
    # based on what is available.
    pasteobj = None
    replytoobj = None
    replylast = None
    replies = None
    replycount = None

    if pasteidarg is not None:
        # Check for id aliases.
        id_alias = {
            'top': view_top,
            'latest': view_latest,
            'all': view_latest
        }
        if pasteidarg in id_alias.keys():
            return id_alias[pasteidarg](request)

        # Lookup existing paste by id.
        pasteobj = get_object(wp_paste.objects,
                              paste_id=pasteidarg,
                              disabled=False)

        if pasteobj is None:
            # Return a 404, that paste cannot be found.
            errmsg = 'Paste not found: {}'.format(pasteidarg)
            return responses.error404(request, errmsg)
        elif (not request.user.is_staff) and pasteobj.is_expired():
            errmsg = 'Paste is expired: {}'.format(pasteidarg)
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
            errmsg = 'Paste is disabled: {}'.format(replytoidarg)
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
        'paste': pasteobj,
        'replyto': replytoobj,
        'replylast': replylast,
        'replies': replies,
        'replycount': replycount,
        'replymax': REPLYMAX,
    }
    return responses.clean_response(
        'paste/index.html',
        context=context,
        request=request)


def view_paste_raw(request):
    """ View a paste as plain text. """
    pasteidarg = responses.get_request_arg(request, 'id')
    if not pasteidarg:
        # /paste/raw doesn't provide anything by itself.
        return responses.error404(request, 'No paste id provided.')

    try:
        pasteobj = wp_paste.objects.get(
            paste_id=pasteidarg,
            disabled=False)
    except wp_paste.DoesNotExist:
        return responses.error404(request, 'Paste not found.')
    except Exception as ex:
        log.error('Error retrieving paste: {}\n{}'.format(pasteidarg, ex))
        return responses.error404(request, 'Paste not found.')

    if pasteobj is None:
        return responses.error404(request, 'Paste content not found.')
    elif (not request.user.is_staff) and pasteobj.is_expired():
        # Staff may view expired pastes.
        return responses.error404(request, 'Paste is expired.')

    try:
        pasteobj.view_count += 1
        pasteobj.save()
    except Exception as ex:
        log.error('Unable to update view_count!\n{}'.format(ex))
    try:
        content = pasteobj.content
    except Exception as ex:
        log.error('paste.content is not available!\n{}'.format(ex))
        return responses.error404(request, 'Paste content not found.')

    # Valid paste, return the plain content.
    return responses.text_response(content)


@never_cache
@csrf_protect
def view_replies(request):
    """ View all replies for a paste. """
    pasteidarg = responses.get_request_arg(request, 'id')
    if pasteidarg is None:
        return responses.error404(request, 'No paste id given.')

    pasteobj = get_object(wp_paste.objects,
                          paste_id=pasteidarg,
                          disabled=False)
    if pasteobj is None:
        # No paste found.
        errmsg = 'Paste not found: {}'.format(pasteidarg)
        return responses.error404(request, errmsg)

    replies = pasteobj.children.order_by('-publish_date')
    context = {
        'paste': pasteobj,
        'replies': replies,
    }

    return responses.clean_response(
        'paste/replies.html',
        context=context,
        request=request)


@never_cache
@csrf_protect
def view_top(request):
    """ View top pastes (highest view count) """

    return list_view(request, title='Top Pastes', orderby='-view_count')
