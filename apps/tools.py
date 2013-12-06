""" Welborn Productions - Apps - Tools
    Provides various tools for dealing with apps (wp sub-apps).
    -Christopher Welborn 2013
"""
import os.path
import sys

from django.conf import settings

from wp_main.utilities.wp_logging import logger
_log = logger('apps.tools').log


class AppInfo(object):

    """ Holds basic app info. """

    def __init__(self, **kwargs):
        """ Initializes an AppInfo.
            Keyword Arguments:
                alias        : Alias for this app.
                description  : Short description.
                longdesc     : Long description.
                name         : Name.
                version      : Version string (X.X.X)
        """

        for skey, val in kwargs.items():
            try:
                setattr(self, skey, val)
            except Exception as ex:
                _log.error('Unable to set attribute: {}\n{}'.format(skey, ex))


def get_appdir(appname, relative=False):
    """ Retrieves dir for app by appname.
        Keyword Arguments:
            relative  : Return relative dir to BASE_PARENT instead of absolute.
                        Default: False
    """
    appname = appname.lower()
    appmod = get_appmodule(appname)
    if hasattr(appmod, '__file__'):
        appinit = getattr(appmod, '__file__')
        if appinit:
            appdir = os.path.split(appinit)[0]
            if relative:
                appdir = appdir.replace(settings.BASE_PARENT, '')
            return appdir
    return None


def get_appgitdir(appname, branch=None):
    """ Retrieves github.com dir for welbornprod/wp_site for an app by name.
        If branch is None then the 'master' branch is used.
    """

    appdir = get_appdir(appname, True)
    if not appdir:
        return None
    if not branch:
        branch = 'master'
    gitbase = os.path.join('/welbornprod/wp_site/tree', branch)
    # Trim wp_site, to rejoin with github base.
    slicer = 2 if appdir.startswith('/') else 1
    reldir = '/'.join(appdir.split('/')[slicer:])
    return os.path.join(gitbase, reldir)


def get_appinfo(appname):
    """ Retrieves an AppInfo() for an app by name. """
    appname = appname.lower()
    appmod = get_appmodule(appname)
    if not appmod:
        return None
    appinfo = {}
    for aname in [a for a in dir(appmod) if a.startswith('app_')]:
        appinfo[aname] = getattr(appmod, aname)

    return AppInfo(**appinfo)


def get_appmodule(appname):
    if 'apps' in sys.modules.keys():
        appsmod = sys.modules['apps']
    else:
        # Django not initialized.
        return None

    appname = appname.lower()
    if not hasattr(appsmod, appname):
        raise ValueError('No app named: {}'.format(appname))

    appmod = getattr(appsmod, appname)
    return appmod


def get_apps(printdebug=False):
    if 'apps' in sys.modules.keys():
        appsmod = sys.modules['apps']
    else:
        # Django not initialized.
        return []
    appinfo = []
    for aname in [a for a in dir(appsmod) if not a.startswith('_')]:
        if printdebug:
            print('checking attribute on apps: {}'.format(aname))

        aval = getattr(appsmod, aname)
        # Check for sub-app attributes.
        subappinfo = {}
        for subattr in [at for at in dir(aval) if at.startswith('app_')]:
            # These are all sub-app attributes of the 'app_ATTR' kind.
            shortname = subattr.split('_')[1]
            subappinfo[shortname] = getattr(aval, subattr)
        if subappinfo:
            appinfo.append(AppInfo(**subappinfo))
    return appinfo


def print_dict(d, indention=0):
    """ Pretty prints a dict. """
    spacing = (' ' * indention)
    if isinstance(d, dict):
        for skey in sorted(d.keys()):
            val = d[skey]
            if isinstance(val, dict):
                print('{}{}:'.format(spacing, skey))
                print_dict(val, indention=indention + 4)
            else:
                print('{}{}: {}'.format(spacing, skey, str(val)))
    else:
        print('{}{}'.format(spacing, str(d)))


def cmdline_test():
    """ Just a test to see if certain functions are working. """
    # Print all app info.
    for subappinfo in get_apps():
        # Print attributes for this sub app.
        for attr, val in subappinfo.items():
            print('    {}: {}'.format(attr, val))
    return 0


if __name__ == '__main__':
    exit(cmdline_test())
