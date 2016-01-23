'''django_startup.py

    Ensures that django environment is ready to be used by other scripts.
    Whether its from the command-line or from the running django app.
    Created on Nov 1, 2013

@author: Christopher Welborn
'''

import sys
import os

NAME = 'DjangoInit'
__version__ = '1.0.4'


# Exportable attributes..
# These are only set when initialize_django() successfully completes.
project_dir = ''
settings_dir = ''
scripts_dir = ''
initialized = False
# Path to django installation.
django_path = '/usr/local/lib/python{}.{}/dist-packages/django'.format(
    sys.version_info.major,
    sys.version_info.minor
)


def get_root_parent(scriptpath):
    """ Retrieves the parent dir for the whole project.
        This is a good place to start building relative
        paths. It has to do this without django.conf.settings.BASE_DIR.
    """

    if '/' not in scriptpath:
        return None

    if 'wp_site' not in scriptpath:
        # Maybe this is the parent (it is for remote-servers since 3.3)
        if os.path.isdir(os.path.join(scriptpath, 'wp_site')):
            # This is the parent.
            return scriptpath

        # Nope, no parent here.
        print('\nInvalid path for this project: {}'.format(scriptpath))
        print('No wp_site dir found!')
        return None

    # retrieve parent dirs, and append the 'wp_site' we're looking for.
    parts = scriptpath.split('/')
    if parts.count('wp_site') == 1:
        parent = '/'.join(parts[:parts.index('wp_site')])
    elif parts.count('wp_site') > 1:
        parent = '/'.join(parts[:parts.index('wp_site') + 1])

    return parent


def init_django():
    """ Gets the django environment for wp_site up and running so django
        modules can be used properly.
    """
    global project_dir, settings_dir, scripts_dir, initialized

    # Set required environment variable (if not set already.)
    if not os.environ.get('DJANGO_SETTINGS_MODULE', False):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'wp_main.settings'

    # Find first real sys.path (first is empty sometimes from cmdline)
    for paths in sys.path:
        if paths:
            scriptpath = paths
            break

    project_parent = get_root_parent(scriptpath)
    if not project_parent:
        # This is bad!
        print('\nCan\'t find project parent from: {}'.format(scriptpath))
        return False

    # These relative paths should be on all sites (dev, test, prod.)
    project_dir = os.path.join(project_parent, 'wp_site')
    settings_dir = os.path.join(project_dir, 'wp_main')
    scripts_dir = os.path.join(project_dir, 'scripts')

    # Make sure all required directories exist.
    for require_dir in (project_dir, settings_dir, scripts_dir):
        if not os.path.isdir(require_dir):
            print('\nUnable to find dir: {}'.format(require_dir))
            return False
        # Insert into sys path if not already there.
        if require_dir not in sys.path:
            sys.path.insert(0, require_dir)

    # Required since 1.7
    import django
    django.setup()

    # Success
    initialized = True
    return True
