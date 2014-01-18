#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Tools - Refresher
     @summary: Builds files that need it with builder.py,
               Refreshes static files (collectstatic),
               refreshes admin css (static/admin/css),
               and Restarts the server.
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 29, 2013
'''

import sys
import os

from docopt import docopt

# Script info...
NAME = 'WpRefresh'
VERSION = '1.2.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
# Initialize Django stuff.
try:
    import django_init
    if not django_init.init_django():
        sys.exit(1)
except ImportError as eximp:
    print('\nMissing django_init.py!:\n{}'.format(eximp))
    sys.exit(1)
except Exception as ex:
    print('\nError initializing django environment!:\n{}'.format(ex))
    sys.exit(1)

# Fix raw_input..
if sys.version < '3':
    input = raw_input  # noqa

# Get Settings..
from django.conf import settings

USAGESTR = """{version}

    Usage:
        wprefresh.py [options]

    Options:
        -A,--noadmin    : Skip admin css copy.
        -b,--buildwp    : Only build wp files.
        -B,--nobuild    : Skip building files.
        -c,--collect    : Auto static collection.
        -C,--nocollect  : Skip static collection.
        -d,--debug      : Prints extra info (not much right now).
        -h,--help       : Show this message.
        -l,--live       : Suppress warning about live site.
        -r,--norestart  : Skip apache restart.
        -R,--restart    : Just restart the server, nothing else.
        -v,--version    : Show version.
""".format(version=VERSIONSTR)


def main(argd):
    # if test is passed no warning is given before restarting the server.
    TEST = ('wp_test' in django_init.project_dir)
    WARN = False if TEST else (not (argd['--live'] or argd['--norestart']))

    # Check for mismatched args..
    mismatched = check_argset(argd,
                              [('--collect', '--nocollect'),
                               ('--nobuild', '--buildwp'),
                               ('--restart', '--collect'),
                               ('--restart', '--buildwp'),
                               ('--restart', '--norestart'),
                               ])
    if mismatched:
        return 1

    # Check overall skip.
    if check_args(argd, ('--norestart',
                         '--nobuild',
                         '--nocollect',
                         '--noadmin')):
        print('\nSkipping entire refresh...')
        return 0

    # Show warning if needed..
    if WARN and (not warn_live()):
        return 0

    # Just restart
    if argd['--restart']:
        check_call(apache_restart)
        return 0

    # Run build files..
    if not argd['--nobuild']:
        check_call(build_files, wponly=argd['--buildwp'])
    # Run collect static
    if not argd['--nocollect']:
        check_call(collect_static, autocollect=argd['--collect'])
    # Run admin copy (overwrites anything in /static)
    if not argd['--noadmin']:
        check_call(collect_admin_css, printskipped=argd['--debug'])
    # Run apache restart
    if not argd['--norestart']:
        check_call(apache_restart)

    return 0


def apache_restart():
    """ Restart the apache server """
    # apache restart locations.
    remote_apache_path = os.path.join(settings.BASE_PARENT, 'apache2', 'bin')
    if os.path.isdir(remote_apache_path):
        apachecmd = ''.join(['. ', remote_apache_path]) + '/'
        use_elevation = False
    else:
        apachecmd = os.path.join('/etc', 'init.d', 'apache2') + ' '
        use_elevation = True
   
    print("\nRestarting apache... (" + apachecmd + 'restart)')
    if (os.path.isfile(apachecmd.strip(' ')) or
       os.path.isdir(apachecmd.strip('/').strip('. '))):
        try:
            if use_elevation:
                apachecmd = 'sudo ' + apachecmd
            callret = os.system(apachecmd + 'restart')
            ret = (callret == 0)
        except Exception as ex:
            print('\nunable to restart apache:\n' + str(ex))
            ret = False
    else:
        print('\napache command not found!: ' + apachecmd + '\n')
        ret = False
    return ret


def build_files(wponly=False):
    """ Build css/js files """
    builder_py = os.path.join(settings.BASE_DIR, 'scripts', 'builder.py')
    if os.path.isfile(builder_py):
        print('\nRunning builder...')
        build_cmd = ['python3', builder_py]
        if wponly:
            # only build wp*.js files. not external stuff. (takes too long)
            build_cmd = build_cmd + ['-i', 'wp', '-f', '-wp']
        print('running: {}'.format(' '.join(build_cmd)))
        callret = os.system(' '.join(build_cmd))
        ret = (callret == 0)
    else:
        print('\nbuilder.py not found!: {}'.format(builder_py))
        ret = False
    return ret


def check_args(argd, arglist):
    """ If all args in arglist are present in argd,
        return True. (Checks for mismatched args)
    """

    values = [argd[a] for a in arglist]
    if all(values):
        print('\nThese args can\'t be used at the same time:')
        print('    {}'.format('\n    '.join(arglist)))
        return True
    return False


def check_argset(argd, argsets):
    """ Checks several sets of args at once. """
    ret = False
    for arglist in argsets:
        if check_args(argd, arglist):
            ret = True
            break
    return ret


def check_call(func, *args, **kwargs):
    """ Check return of a command, exit on failure. """
    if not func(*args, **kwargs):
        print('Command failed: {}'.format(func.__name__))
        sys.exit(1)
    return True


def collect_static(autocollect=False):
    """ Run manage.py collectstatic """
    manage_py = os.path.join(settings.BASE_DIR, "manage.py")
    use_elevation = 'workspace/' in settings.BASE_DIR

    if os.path.isfile(manage_py):
        print("\nRunning collectstatic...")
        collect_cmd = ['echo', '"yes"', '|'] if autocollect else []
        if use_elevation:
            collect_cmd += ['sudo']
        collect_cmd += ['python3', manage_py, 'collectstatic']
        print("running: " + ' '.join(collect_cmd))
        callret = os.system(' '.join(collect_cmd))
        ret = (callret == 0)
    else:
        print("\nmanage.py not found!: " + manage_py + '\n')
        ret = False
    return ret


def collect_admin_css(printskipped=False):
    """ Move admin css to proper dir """
    # admin css dirs (source, target)
    admin_css = os.path.join(django_init.project_dir, "home/static/admin/css")
    admin_css_static = os.path.join(settings.STATIC_ROOT, "admin/css")

    if not admin_css_static.endswith('/'):
        admin_css_static += '/'
    if os.path.isdir(admin_css) and os.path.isdir(admin_css_static):
        print("\nCopying admin css...")
        srcfiles = os.listdir(admin_css)
        for filename in srcfiles:
            srcfile = os.path.join(admin_css, filename)
            dstfile = os.path.join(admin_css_static, filename)
            if copy_file(srcfile, dstfile):
                print('    Copied to: {}'.format(dstfile))
            else:
                if printskipped:
                    print('     Skipping: {}'.format(srcfile))
        ret = True
    else:
        print("\nadmin css directories not found:\n    source: " + admin_css +
              '\n    target: ' + admin_css_static + '\n')
        ret = False
    return ret


def copy_file(srcfile, dstfile):
    """ Copies a single file. """
    use_elevation = 'workspace/' in settings.BASE_DIR
    if is_modified(srcfile, dstfile):
        css_cmd = ['sudo'] if use_elevation else []
        css_cmd += ['cp', srcfile, dstfile]
        callret = os.system(' '.join(css_cmd))
        return (callret == 0)
    return False


def is_modified(srcfile, dstfile):
    """ Returns true if the src file has been modified,
        and the destination file has not (or doesn't exist yet).
    """

    # Have min and original, calculate modified times.
    try:
        srcmod = os.path.getmtime(srcfile)
    except Exception as ex:
        print('\nUnable to stat file: {}'.format(srcfile, ex))
        return False
    try:
        if os.path.isfile(dstfile):
            dstmod = os.path.getmtime(dstfile)
        else:
            # Destination doesn't exit yet.
            return True
    except Exception as ex:
        print('\nUnable to stat file: {}'.format(dstfile, ex))
        return False

    if srcmod > dstmod:
        # Source file is newer than the destination file
        return True

    # destination file is newer than the source file
    return False


def warn_live():
    print('\nYou are working on the ** LIVE SITE ** !')
    print('Continuing will restart the server...')
    warn_response = input('\n    Continue anyway? (y|n): ')
    if not warn_response.lower().startswith('y'):
        print('\nCancelling, goodbye.')
        return False
    return True
    

# START OF SCRIPT ------------------------------------------------------------
if __name__ == '__main__':
    mainargd = docopt(USAGESTR, version=VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)
