#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Tools - Refresher
     @summary: Refreshes static files (collectstatic), refreshes admin css (static/admin/css),
               and Restarts the server.
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 29, 2013
'''

import sys, os, os.path, commands

script_dir = sys.path[0]
project_dir = os.path.split(script_dir)[0]
settings_dir = os.path.join(project_dir, 'wp_main/')
sys.path.insert(0, project_dir)
sys.path.insert(0, settings_dir)

if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'wp_main.settings'

# DJANGO READY.
print "django environment ready."

# Get Settings..
from django.conf import settings

#admin css dirs (source, target)
admin_css = os.path.join(project_dir, "home/static/admin/css")
admin_css_static = os.path.join(settings.STATIC_PARENT, "static/admin/css")
if not admin_css_static.endswith('/'): admin_css_static += '/'

# location of manage.py
manage_py = os.path.join(settings.BASE_DIR, "manage.py")

# apache restart locations.
remote_apache_path = os.path.join(settings.STATIC_PARENT, 'apache2', 'bin')
if os.path.isdir(remote_apache_path):
    apachecmd = ''.join(['.', remote_apache_path])
    use_elevation = False
else:
    apachecmd = os.path.join('/etc', 'init.d','apache2') + ' '
    use_elevation = True

def main(args):
    global apachecmd
    
    # if test is passed we will work on the test site, otherwise it will be live.
    TEST_SITE = ("test" in args) or ("-t" in args) or ("--test" in args)
    # explicitly passing these disables the warning about refreshing a LIVE site.
    WARN_LIVE = (not "live" in args) and (not "-l" in args) and (not "--live" in args)
    # say yes automatically to collectstatic if 'yes' is passed.
    AUTO_COLLECT = ('yes' in args) or ('-y' in args) or ('--yes' in args)
    
    # WARN LIVE SITE
    if (not TEST_SITE) and WARN_LIVE:
        print "\nYou are refreshing the ** LIVE SITE ** !"
        warn_response = raw_input("\n    Continue anyway? (y|n): ")
        if not warn_response.lower().startswith('y'):
            print "\nCancelling, goodbye."
            return 0
        
    # COLLECTSTATIC
    if os.path.isfile(manage_py):
        print "\nRunning collectstatic..."
        collect_cmd = ['echo', '"yes"', '|'] if AUTO_COLLECT else []
        collect_cmd += ['python', manage_py, 'collectstatic']
        os.system(' '.join(collect_cmd))
    else:
        print "\nmanage.py not found!: " + manage_py + '\n'
    
    # COLLECT ADMIN CSS
    if os.path.isdir(admin_css) and os.path.isdir(admin_css_static):
        print "\nCopying admin css..."
        css_cmd = ('sudo', 'cp', os.path.join(admin_css, '*'), admin_css_static)
        os.system(' '.join(css_cmd))
    else:
        print "\nadmin css directories not found:\n    source: " + admin_css + \
              '\n    target: ' + admin_css_static + '\n'
    
   
    # RESTART APACHE
    print "\nRestarting apache... (" + apachecmd + 'restart)'
    if os.path.isfile(apachecmd.strip(' ')):
        try:
            if use_elevation: apachecmd = 'sudo ' + apachecmd
            os.system(apachecmd + 'restart')
        except Exception as ex:
            print '\nunable to restart apache:\n' + str(ex)
    else: 
        print '\napache command not found!: ' + apachecmd + '\n'
        
    print "\nFinished.\n"
        
if __name__ == '__main__':
    args = sys.argv[1:]
    sys.exit(main(args))

