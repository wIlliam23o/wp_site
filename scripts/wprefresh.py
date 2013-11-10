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

import sys
import os

script_dir = sys.path[0]
project_dir = os.path.split(script_dir)[0]
settings_dir = os.path.join(project_dir, 'wp_main/')
sys.path.insert(0, project_dir)
sys.path.insert(0, settings_dir)

if not 'DJANGO_SETTINGS_MODULE' in os.environ.keys():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'wp_main.settings'

# DJANGO READY.
print "django environment ready."

# Get Settings..
from django.conf import settings

# admin css dirs (source, target)
admin_css = os.path.join(project_dir, "home/static/admin/css")
admin_css_static = os.path.join(settings.STATIC_PARENT, "static/admin/css")
if not admin_css_static.endswith('/'):
    admin_css_static += '/'

# location of manage.py, builder.py
manage_py = os.path.join(settings.BASE_DIR, "manage.py")
builder_py = os.path.join(settings.BASE_DIR, 'scripts', 'builder.py')

# apache restart locations.
remote_apache_path = os.path.join(settings.STATIC_PARENT, 'apache2', 'bin')
if os.path.isdir(remote_apache_path):
    apachecmd = ''.join(['. ', remote_apache_path]) + '/'
    use_elevation = False
else:
    apachecmd = os.path.join('/etc', 'init.d', 'apache2') + ' '
    use_elevation = True


def main(args):
    global apachecmd
    
    # if test is passed we will work on the test site, otherwise it will be live.
    TEST_SITE = ('wp_test' in project_dir)
    # refreshes can be forced
    AUTO_LIVE = ('live' in args) or ('-l' in args) or ('--live' in args)
    AUTO_COLLECT = ('yes' in args) or ('-y' in args) or ('--yes' in args)
    # refreshes can be skipped
    SKIP_COLLECT = ('no' in args) or ('-n' in args) or ('--nocollect' in args) or ('--nostatic' in args)
    SKIP_REFRESH = ('skip' in args) or ('-s' in args) or ('--skiprefresh' in args) or ('--norefresh' in args) or ('--noapache' in args)
    WARN_LIVE = False if TEST_SITE else (not (AUTO_LIVE or SKIP_REFRESH))
    # build can be skipped
    SKIP_BUILD = ('-b' in args) or ('--nobuild' in args) or ('skipbuild' in args)
    BUILD_ALL_JS = ('-j' in args) or ('--alljs' in args) or ('buildall' in args)
    SKIP_ALL = (SKIP_COLLECT and SKIP_REFRESH and SKIP_BUILD)
    
    # Ambiguous args
    if SKIP_COLLECT and AUTO_COLLECT:
        print('\nBoth \'yes\' and \'no\' args used, this won\'t work.')
        sys.exit(1)
    if AUTO_LIVE and SKIP_REFRESH:
        print('\nBoth \'live\' and \'skip\' args used, this won\'t work.')
        sys.exit(1)
    if SKIP_ALL:
        print('\nSkipping collectstatic, apache refresh, and build...')
        sys.exit(0)
    # WARN LIVE SITE
    if WARN_LIVE:
        print "\nYou are refreshing the ** LIVE SITE ** !"
        warn_response = raw_input("\n    Continue anyway? (y|n): ")
        if not warn_response.lower().startswith('y'):
            print "\nCancelling, goodbye."
            return 0
    
    # BUILD
    if SKIP_BUILD:
        print('\nSkipping build...')
    else:
        if os.path.isfile(builder_py):
            print('\nRunning builder...')
            build_cmd = ['python', builder_py]
            if not BUILD_ALL_JS:
                # only build wp*.js files. not external stuff. (takes too long)
                build_cmd = build_cmd + ['-i', 'wp', '-f', '-wp']
            print('running: {}'.format(' '.join(build_cmd)))
            os.system(' '.join(build_cmd))
        else:
            print('\nbuilder.py not found!: {}'.format(builder_py))
        
    # COLLECTSTATIC
    if SKIP_COLLECT:
        print('\nSkipping collectstatic...')
    else:
        if os.path.isfile(manage_py):
            print("\nRunning collectstatic...")
            collect_cmd = ['echo', '"yes"', '|'] if AUTO_COLLECT else []
            if use_elevation:
                collect_cmd += ['sudo']
            collect_cmd += ['python', manage_py, 'collectstatic']
            print("running: " + ' '.join(collect_cmd))
            os.system(' '.join(collect_cmd))
        else:
            print("\nmanage.py not found!: " + manage_py + '\n')
        
        # COLLECT ADMIN CSS
        if os.path.isdir(admin_css) and os.path.isdir(admin_css_static):
            print("\nCopying admin css...")
            css_cmd = ['sudo'] if use_elevation else []
            css_cmd += ['cp', os.path.join(admin_css, '*'), admin_css_static]
            os.system(' '.join(css_cmd))
        else:
            print("\nadmin css directories not found:\n    source: " + admin_css +
                  '\n    target: ' + admin_css_static + '\n')
    
    # RESTART APACHE
    if SKIP_REFRESH:
        print('\nSkipping apache restart...')
    else:
        print("\nRestarting apache... (" + apachecmd + 'restart)')
        if os.path.isfile(apachecmd.strip(' ')) or os.path.isdir(apachecmd.strip('/').strip('. ')):
            try:
                if use_elevation:
                    apachecmd = 'sudo ' + apachecmd
                os.system(apachecmd + 'restart')
            except Exception as ex:
                print('\nunable to restart apache:\n' + str(ex))
        else:
            print('\napache command not found!: ' + apachecmd + '\n')
            
        print("\nFinished.\n")
        
if __name__ == '__main__':
    args = sys.argv[1:]
    sys.exit(main(args))
