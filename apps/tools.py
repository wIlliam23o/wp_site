""" Welborn Productions - Apps - Tools
    Provides various tools for dealing with apps (wp sub-apps).
    -Christopher Welborn 2013
"""

import logging
log = logging.getLogger('wp.apps.tools')

from apps.models import wp_app


def get_appgitdir(appname, branch=None):
    """ Retrieves github.com dir for welbornprod/wp_site for an app by name.
        If branch is None then the 'master' branch is used.
    """

    if not branch:
        branch = 'master'
    gitdir = '/welbornprod/wp_site/tree/{}/apps/{}'.format(branch, appname)
    return gitdir


def get_apps(printdebug=False):
    """ Return all apps or None. """

    try:
        apps = wp_app.objects.filter(disabled=False)
    except Exception as ex:
        log.error('Unable to get apps:\n{}'.format(ex))
        return None
    return apps.order_by('name')


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
    for subapp in get_apps():
        # Print attributes for this sub app.
        print('name: {}, version: {}'.format(subapp.name, subapp.version))
        print('    json: {}'.format(subapp.json_data))
        print('    desc: {}'.format(subapp.description))

    return 0


if __name__ == '__main__':
    exit(cmdline_test())
