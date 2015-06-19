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
VERSION = '2.0.0'
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

# Get Django Settings and Cache to work with..
from django.conf import settings
from django.core.cache import cache

USAGESTR = """{version}

    Usage:
        wprefresh.py [options]

    Options:
        -A,--noadmin         : Skip admin css copy.
        -C,--nocollect       : Skip static collection.
        -d,--debug           : Prints extra info (not much right now).
        -h,--help            : Show this message.
        -k,--clearcache      : Clear Django's cache for the WP site.
        -l,--live            : Suppress warning about live site.
        -r,--restart         : Just restart the server, nothing else.
        -R,--norestart       : Skip apache restart.
        -t,--admintemplates  : Refresh admin templates also.
        -v,--version         : Show version.
""".format(version=VERSIONSTR)


def main(argd):
    # if test is passed no warning is given before restarting the server.
    test = ('wp_test' in django_init.project_dir)
    warn = False if test else (not (argd['--live'] or argd['--norestart']))

    # Check for mismatched args (rather than write a complicated USAGESTR)..
    mismatched = check_argset(argd, [('--restart', '--norestart')])
    if mismatched:
        return 1

    # Check overall skip.
    if check_args(argd,
                  ('--norestart', '--nocollect', '--noadmin'),
                  unless=('--clearcache',)):
        print('\nSkipping entire refresh...')
        return 0

    # Show warning if needed..
    if warn and (not warn_live()):
        return 0

    # Just restart
    if argd['--restart']:
        check_call(apache_restart)
        return 0

    # Run collect static
    if not argd['--nocollect']:
        check_call(collect_static)
    # Run admin copy (overwrites anything in /static)
    if not argd['--noadmin']:
        check_call(collect_admin_css, printskipped=argd['--debug'])
        if argd['--admintemplates']:
            check_call(collect_admin_templates, printskipped=argd['--debug'])
    # Run apache restart
    if not argd['--norestart']:
        check_call(apache_restart)

    if argd['--clearcache']:
        check_call(clear_cache)

    return 0


def apache_restart():
    """ Restart the apache server """
    # apache restart locations.
    remote_apache_path = os.path.join(settings.BASE_PARENT, 'apache2', 'bin')
    if os.path.isdir(remote_apache_path):
        # Remote: `../apache2/bin/restart`
        apachecmd = ''.join(['. ', remote_apache_path]) + '/'
        use_elevation = False
    else:
        # Local: `apache2 restart`
        apachecmd = os.path.join('/etc', 'init.d', 'apache2') + ' '
        use_elevation = True

    print('\nRestarting apache... ({}restart)'.format(apachecmd))
    if not (
            os.path.isfile(apachecmd.strip(' ')) or
            os.path.isdir(apachecmd.strip('/').strip('. '))):
        print('\napache command not found!: {}\n'.format(apachecmd))
        return False

    try:
        if use_elevation:
            apachecmd = 'sudo ' + apachecmd
        callret = os.system(apachecmd + 'restart')
        ret = (callret == 0)
    except Exception as ex:
        print('\nunable to restart apache:\n' + str(ex))
        ret = False

    return ret


def build_files(wponly=False):
    """ Build css/js files """
    builder_py = os.path.join(settings.BASE_DIR, 'scripts', 'builder.py')
    if not os.path.isfile(builder_py):
        print('\nbuilder.py not found!: {}'.format(builder_py))
        return False

    print('\nRunning builder...')
    build_cmd = ['python3', builder_py]
    if settings.SITE_VERSION.lower().startswith('local'):
        build_cmd.insert(0, 'sudo')

    if wponly:
        # only build wp*.js files. not external stuff. (takes too long)
        build_cmd = build_cmd + ['-i', 'wp', '-f', '-wp']
    print('running: {}'.format(' '.join(build_cmd)))
    callret = os.system(' '.join(build_cmd))
    return (callret == 0)


def check_args(argd, arglist, unless=None):
    """ If all args in arglist are present in argd,
        return True. (Checks for mismatched args)
        If unless is given, the args can be present as long as the
        'unless' arguments are also present.
        Arguments:
            argd     : Docopt style argument dict.
            arglist  : Tuple/List of arguments to check.
            unless   : Tuple/List of arguments that make the presence of all
                       other arguments okay.
    """

    argsgiven = all([argd[a] for a in arglist])
    unlessvals = [argd[a] for a in unless] if unless else []
    unlessgiven = all(unlessvals) if unlessvals else False

    if argsgiven:
        if unless and unlessgiven:
            # The unless args were given, and present. So we're okay.
            return False
        # Args were present, no unless given or no unless present.
        print('\nThese args can\'t be used at the same time:')
        print('    {}'.format('\n    '.join(arglist)))
        if unless:
            print('\nUnless these args are used:')
            print('    {}'.format('\n    '.join(unless)))
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


def clear_cache():
    """ Clear Django's cache. """

    try:
        print('\nClearing the cache...')
        cache.clear()
    except Exception as ex:
        print('\nError clearing the cache:\n{}'.format(ex))
        return False
    print('\nCache was cleared.')
    return True


def collect_static():
    """ Run manage.py collectstatic """
    manage_py = os.path.join(settings.BASE_DIR, "manage.py")
    use_elevation = 'workspace/' in settings.BASE_DIR

    if not os.path.isfile(manage_py):
        print("\nmanage.py not found!: " + manage_py + '\n')
        return False

    print("\nRunning collectstatic...")
    collect_cmd = ['sudo'] if use_elevation else []
    collect_cmd.extend(['python3', manage_py, 'collectstatic', '--noinput'])

    cmdstr = ' '.join(collect_cmd)
    print('running: {}'.format(cmdstr))
    callret = os.system(cmdstr)

    return (callret == 0)


def collect_admin_css(printskipped=False):
    """ Move admin css to proper dir """
    # admin css dirs (source, target)
    admin_css = os.path.join(django_init.project_dir, 'home/static/admin/css')
    admin_css_static = os.path.join(settings.STATIC_ROOT, 'admin/css')

    if not admin_css_static.endswith('/'):
        admin_css_static += '/'

    if not (os.path.isdir(admin_css) and os.path.isdir(admin_css_static)):
        print('\n'.join((
            'admin css directories not found:',
            '    source: {src}',
            '    target: {dest}\n')).format(
                src=admin_css,
                dest=admin_css_static))
        return False

    print('\nCopying admin css...')
    srcfiles = os.listdir(admin_css)
    for filename in srcfiles:
        srcfile = os.path.join(admin_css, filename)
        dstfile = os.path.join(admin_css_static, filename)
        if copy_file(srcfile, dstfile):
            print('    Copied to: {}'.format(dstfile))
        else:
            if printskipped:
                print('     Skipping: {}'.format(srcfile))
    return True


def collect_admin_templates(printskipped=False):
    """ Move admin templates to proper dir if they have changed. """
    # admin css dirs (source, target)
    admin_dest = os.path.join(
        django_init.project_dir,
        'wp_main/templates/admin'
    )

    pyver = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
    admin_src = '/'.join((
        '/usr/local/lib/python{}/dist-packages'.format(pyver),
        'django/contrib/admin/templates/admin'
    ))

    if not (os.path.isdir(admin_dest) and os.path.isdir(admin_src)):
        print('\n'.join((
            '',
            'admin template directories not found:'
            '    source: {src}',
            '    target: {dest}\n')).format(
                src=admin_src,
                dest=admin_dest))

        return False

    change_files = ('change_list_results.html',)
    change_msg = 'This file must be edited again!'

    print('\nCopying admin templates from: {}'.format(admin_src))
    srcfiles = os.listdir(admin_src)
    for filename in srcfiles:
        srcfile = os.path.join(admin_src, filename)
        dstfile = os.path.join(admin_dest, filename)
        if copy_file(srcfile, dstfile, nosudo=True):
            print('    Copied to: {}'.format(dstfile))
            if filename in change_files:
                print('               ** {} **'.format(change_msg))
        else:
            if printskipped:
                print('     Skipping: {}'.format(srcfile))
    return True


def copy_file(srcfile, dstfile, nosudo=False):
    """ Copies a single file. """
    use_elevation = ('workspace/' in settings.BASE_DIR) and (not nosudo)
    if is_modified(srcfile, dstfile):
        cp_cmd = ['sudo'] if use_elevation else []
        cp_cmd += ['cp', '-r', srcfile, dstfile]
        callret = os.system(' '.join(cp_cmd))
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
