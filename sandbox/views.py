import logging

from wp_main.utilities import responses

# logging
log = logging.getLogger('wp.sandbox')

sandboxmsg = [
    'The sandbox is for private use.',
    'You wouldn\'t like it anyway...']


@responses.staff_required(user_error=sandboxmsg)
def view_index(request):
    """ Landing page for the sandbox. Nothing important. """
    context = None
    return responses.clean_response('sandbox/index.html', context)


@responses.staff_required(user_error=sandboxmsg)
def view_alert(request):
    """ Testing the alert/notice/attention/approved system messages. """
    link = """
    <a href='/' title='Go home.'>
        <span class='alert_message'>
            That won't work. Click here to go back.
        </span>
    </a>
    """
    context = {
        'alert_title': 'Major Error',
        'alert_content': link
    }
    return responses.clean_response('sandbox/index.html', context)


@responses.staff_required(user_error=sandboxmsg)
def view_notice(request):
    """ Testing alert classes. """
    context = {
        'alert_message': 'Your karma has been updated.',
        'alert_class': 'notice',
    }
    return responses.clean_response('sandbox/index.html', context)
