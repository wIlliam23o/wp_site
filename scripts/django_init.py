'''django_startup.py
    
    Ensures that django environment is ready to be used by other scripts.
    Created on Nov 1, 2013

@author: Christopher Welborn
'''

import sys
import os

_VERSION = '1.0.0'


# Append project's settings.py dir.
def initialize_django(scriptpath):
    project_dir = os.path.split(scriptpath)[0]
    settings_dir = os.path.join(project_dir, "wp_main/")
    if not os.path.isdir(settings_dir):
        print('\nUnable to find dir: {}'.format(os.path.join(project_dir, 'wp_main/')))
        return False
    if not settings_dir in sys.path: 
        sys.path.insert(0, settings_dir)
    if not project_dir in sys.path: 
        sys.path.insert(0, project_dir)
    # Set django environment variable (if not set yet)
    if not 'DJANGO_SETTINGS_MODULE' in os.environ.keys():
        os.environ["DJANGO_SETTINGS_MODULE"] = "wp_main.settings"
    return True

init_django = initialize_django
