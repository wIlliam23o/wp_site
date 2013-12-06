from django import template
register = template.Library()

from wp_main.utilities.wp_logging import logger
from apps import tools as apptools

_log = logger('apps.tags').log


def gitdir(appname):
    """ Retrieves github directory for app by appname.
        If '/' is found in the appname, the appname is interpreted as:
        appname/git-branch
        So 'myapp/dev' will retrieve the dev branch for 'myapp'

        Otherwise the master branch is used.
    """
    if appname.count('/') == 1:
        appname, gitbranch = appname.split('/')
    else:
        gitbranch = 'master'

    try:
        sgitdir = apptools.get_appgitdir(appname, branch=gitbranch)
    except Exception as ex:
        appinfo = 'appname: {}, branch: {}'.format(appname, gitbranch)
        _log.error('Error getting git dir: {}\n{}'.format(appinfo, ex))
        return None
    return sgitdir

registered = (gitdir,)

# register all filters in the registered tuple.
for func in registered:
    register.filter(func.__name__, func)
