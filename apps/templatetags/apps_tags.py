from django import template
register = template.Library()

from wp_main.utilities.wp_logging import logger
from apps import tools as apptools

_log = logger('apps.tags').log


def gitdir(appname):
    """ Retrieves github directory for app by appname. """
    try:
        sgitdir = apptools.get_appgitdir(appname)
    except Exception as ex:
        _log.error('Error getting git dir: {}\n{}'.format(appname, ex))
        return None
    return sgitdir

registered = (gitdir,)

# register all filters in the registered tuple.
for func in registered:
    register.filter(func.__name__, func)
