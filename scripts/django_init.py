'''django_startup.py
    
    Ensures that django environment is ready to be used by other scripts.
    Created on Nov 1, 2013

@author: Christopher Welborn
'''

import sys
import os

NAME = 'DjangoInit'
_VERSION = '1.0.1'


# Exportable attributes..
project_dir = ''
settings_dir = ''
scripts_dir = ''
initialized = False


def initialize_django(scriptpath):
    global project_dir, settings_dir, scripts_dir, initialized

    # Set django environment variable (if not set yet)
    if not 'DJANGO_SETTINGS_MODULE' in os.environ.keys():
        os.environ["DJANGO_SETTINGS_MODULE"] = "wp_main.settings"

    # This usually only happens in the interpreter.
    # We will use the cwd...
    if not scriptpath:
        scriptpath = os.getcwd()

    # Get base directories..
    if scriptpath.endswith('scripts'):
        project_dir = os.path.split(scriptpath)[0]
    else:
        project_dir = scriptpath

    settings_dir = os.path.join(project_dir, "wp_main")
    scripts_dir = os.path.join(project_dir, 'scripts')

    # Make sure all required directories exist.
    for require_dir in (project_dir, settings_dir, scripts_dir):
        if not os.path.isdir(require_dir):
            print('\nUnable to find dir: {}'.format(require_dir))
            return False
    
    # Insert paths for this project (if they aren't already in there)
    if not settings_dir in sys.path:
        sys.path.insert(0, settings_dir)
    if not project_dir in sys.path:
        sys.path.insert(0, project_dir)
    if not scripts_dir in sys.path:
        sys.path.insert(0, scripts_dir)

    # Success
    initialized = True
    return True
# Aliases..
init_django = initialize_django
django_init = initialize_django


def import_settings():
    """ Retrieve django.conf.settings.... """
    if not initialized:
        if not django_init(sys.path[0]):
            return None

    # Django is initialized, try to retrieve django.conf.settings
    try:
        from django.conf import settings
    except ImportError as eximp:
        print('\nUnable to import django settings!:\n{}'.format(eximp))
        return None

    # Return the settings module.
    return settings
