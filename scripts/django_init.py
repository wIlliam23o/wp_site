'''django_startup.py
    
    Ensures that django environment is ready to be used by other scripts.
    Created on Nov 1, 2013

@author: Christopher Welborn
'''

import sys
import os

_VERSION= '1.0.0'
# Append project's settings.py dir.
def initialize_django(scriptpath):
    project_dir = os.path.split(scriptpath)[0]
    settings_dir = os.path.join(project_dir, "wp_main/")
    if not settings_dir in sys.path: 
        sys.path.insert(0, settings_dir)
    if not project_dir in sys.path: 
        sys.path.insert(0, project_dir)
    # Set django environment variable (if not set yet)
    if not os.environ.has_key("DJANGO_SETTINGS_MODULE"):
        os.environ["DJANGO_SETTINGS_MODULE"] = "wp_main.settings"
init_django = initialize_django

def get_scriptfile(argv0):
    shortname = os.path.split(argv0)[1]
    return shortname[:-3] if shortname.endswith('.py') else shortname
