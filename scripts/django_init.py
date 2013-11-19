'''django_startup.py
    
    Ensures that django environment is ready to be used by other scripts.
    Created on Nov 1, 2013

@author: Christopher Welborn
'''

import sys
import os

NAME = 'DjangoInit'
_VERSION = '1.0.3'


# Exportable attributes..
# These are only set when initialize_django() successfully completes.
project_dir = ''
settings_dir = ''
scripts_dir = ''
initialized = False


def get_root_parent(scriptpath):
    """ Retrieves the parent dir for the whole project.
        This is a good place to start building relative
        paths.
    """

    if not '/' in scriptpath:
        return None

    if not 'wp_site' in scriptpath:
        # Maybe this is the parent (it is for remote-servers sometimes)
        parent = os.path.join(scriptpath, 'wp_site')
        if os.path.isdir(parent):
            return parent
        # Nope, no parent here.
        print('\nInvalid path for this project: {}'.format(scriptpath))
        print('No wp_site dir found!')
        return None

    # retrieve parent dirs, and append the 'wp_site' we're looking for.
    parts = scriptpath.split('/')
    parent = '/'.join(parts[:parts.index('wp_site')])
    return parent


def initialize_django():
    global project_dir, settings_dir, scripts_dir, initialized

    # Set environment variable (if not set already.)
    if not 'DJANGO_SETTINGS_MODULE' in os.environ.keys():
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
    
    # Insert paths for this project (if they aren't already in there)
    # Insert main path.
    if not project_dir in sys.path:
        sys.path.insert(0, project_dir)
    # Insert extra import paths.
    if not settings_dir in sys.path:
        sys.path.insert(0, settings_dir)
    if not scripts_dir in sys.path:
        sys.path.insert(0, scripts_dir)

    # Success
    initialized = True
    return True

# Aliases..
init_django = initialize_django
