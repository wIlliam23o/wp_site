#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Tools - Refresher
     @summary: Refreshes static files (collectstatic),
               refreshes admin css (static/admin/css),
               and Restarts the server.


      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 29, 2013
'''
import inspect
import sys
import os
from contextlib import suppress

from docopt import docopt

# Script info...
NAME = 'WpRefresh'
VERSION = '2.0.4'
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

# Get Django Settings and Cache to work with.
# ...must be imported after django_init!
from django.conf import settings     # noqa
from django.core.cache import cache  # noqa

USAGESTR = """{version}

    Usage:
        wprefresh.py [options]

    Options:
        -A,--noadmin         : Skip admin css copy.
        -C,--nocollect       : Skip static collection.
        -d,--debug           : Prints extra info (not much right now).
        -D,--django          : Refresh django admin css/js/etc. also.
        -h,--help            : Show this message.
        -k,--clearcache      : Clear Django's cache for the WP site.
        -l,--live            : Suppress warning about live site.
        -r,--restart         : Just restart the server, nothing else.
        -R,--norestart       : Skip apache restart.
        -t,--admintemplates  : Refresh admin templates also.
        -v,--version         : Show version.
""".format(version=VERSIONSTR)

# Files to ignore when collecting static files.
STATIC_IGNORE = (
    '_in*',
    'sass',
    '*.scss',
)

DEBUG = False


def main(argd):
    global DEBUG
    DEBUG = argd['--debug']
    # if test is passed no warning is given before restarting the server.
    test = (
        settings.SERVER_LOCATION == 'local' or
        settings.SITE_VERSION.lower() != 'main site'
    )
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
        if argd['--django']:
            check_call(collect_django_admin_files)
        if argd['--admintemplates']:
            check_call(collect_django_admin_templates)
        check_call(collect_admin_files)
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
        elevcmd = ''
        apachecmd = ''.join(['. ', remote_apache_path]) + '/'
        apacheargs = 'restart'
    else:
        # Local: `sudo apache2 restart`
        elevcmd = 'sudo '
        apachecmd = '/etc/init.d/apache2 '
        apacheargs = ' restart'

    restartcmd = ''.join((elevcmd, apachecmd, apacheargs))
    print('\nRestarting apache... ({})'.format(restartcmd))
    if not (
            os.path.isfile(apachecmd.strip(' ')) or
            os.path.isdir(apachecmd.strip('/').strip('. '))):
        print_err('\nApache command not found!: {}\n'.format(apachecmd))
        return False

    try:
        callret = os.system(restartcmd)
        ret = (callret == 0)
    except Exception as ex:
        print_err('\nUnable to restart apache:\n' + str(ex))
        ret = False

    return ret


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
        print_err('\nThese args can\'t be used at the same time:')
        print_err('    {}'.format('\n    '.join(arglist)))
        if unless:
            print_err('\nUnless these args are used:')
            print_err('    {}'.format('\n    '.join(unless)))
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
        print_err('WpRefresh command failed: {}'.format(func.__name__))
        sys.exit(1)
    return True


def clear_cache():
    """ Clear Django's cache. """

    try:
        print('\nClearing the cache...')
        cache.clear()
    except Exception as ex:
        print_err('\nError clearing the cache:\n{}'.format(ex))
        return False
    print('\nCache was cleared.')
    return True


def collect_static():
    """ Run manage.py collectstatic """
    manage_py = os.path.join(settings.BASE_DIR, 'manage.py')

    if not os.path.isfile(manage_py):
        print_err("\nmanage.py not found!: " + manage_py + '\n')
        return False

    print("\nRunning collectstatic...")
    # No user input when running wprefresh.
    collect_cmd = ['python3', manage_py, 'collectstatic', '--noinput']
    # Add all ignored patterns.
    for globpat in STATIC_IGNORE:
        collect_cmd.extend(('--ignore', globpat))

    cmdstr = ' '.join(collect_cmd)
    print('running: {}'.format(cmdstr))
    callret = os.system(cmdstr)

    return (callret == 0)


def collect_admin_files():
    """ Move admin files to the proper static dir for serving.
        Possibly raises CopyError or CreateError.
    """
    # admin css dirs (source, target)
    admin_path = os.path.join(django_init.project_dir, 'static/admin')
    admin_destpath = os.path.join(settings.STATIC_ROOT, 'admin')
    copy_tree(admin_path, admin_destpath)
    return True


def collect_django_admin_templates():
    """ Move admin templates to proper dir for use.
        Possibly raises CopyError or CreateError.
    """
    # admin css dirs (source, target)
    admin_dest = os.path.join(
        django_init.project_dir,
        'wp_main/templates/admin'
    )
    admin_src = django_src_path('contrib/admin/templates/admin')

    change_files = ('change_list_results.html',)
    change_msg = 'This file must be edited again!'

    print('\nCopying admin templates from: {}'.format(admin_src))
    copied_files = copy_tree(admin_src, admin_dest)
    for copiedfile in copied_files:
        for changefile in change_files:
            if copiedfile.endswith(changefile):
                print_err('** Must be edited again: {} **'.format(copiedfile))
    return True


def collect_django_admin_files():
    """ Collect django's admin css files into /static/admin/css.
        This only needs to run when django has been updated.
        Possibly raises CopyError or CreateError.
    """
    srcpath = django_src_path('contrib/admin/static/admin')
    if not srcpath:
        return False
    destpath = os.path.join(django_init.project_dir, 'static/admin')
    print('\nCopying django admin files...')
    return copy_tree(srcpath, destpath)


def copy_file(srcfile, destfile, force=False):
    """ Copies a single file if it has been modified, or `force` is used.
        Returns the dest. name on copies, and None for non-modified files.
        Raises a CopyError on failure.
    """

    if force or is_modified(srcfile, destfile):
        cp_cmd = ['cp', '-r', srcfile, destfile]
        callret = os.system(' '.join(cp_cmd))
        if callret == 0:
            print('Copied {}\n  {}'.format(srcfile, destfile))
            return destfile
        raise CopyError(src=srcfile, dest=destfile)

    debug('Skipping unmodified file: {}'.format(srcfile))
    return None


def copy_tree(srcpath, destpath):
    """ Copy an entire directory tree.
        Returns a set of copied files for success,
        Raises CopyError or CreateError on failure.
    """
    if not os.path.exists(srcpath):
        raise CopyError(
            src=srcpath,
            ex=FileNotFoundError('Source path does not exist.'))
    create_dir(destpath)
    copied = set()
    for root, dirs, files in os.walk(srcpath):
        relpath = root.replace(srcpath, '').lstrip('/')
        for dirname in dirs:
            destdirname = os.path.join(destpath, relpath, dirname)
            create_dir(destdirname)

        for filename in files:
            destfilename = os.path.join(destpath, relpath, filename)
            filepath = os.path.join(root, filename)
            copiedfile = copy_file(filepath, destfilename)
            if copiedfile:
                copied.add(copiedfile)
    return copied


def create_dir(dirpath):
    """ Create a directory if it doesn't exist.
        Returns a path name for created directories, or None for existing.
        Raises CreateError on failure.
    """
    if not os.path.exists(dirpath):
        debug('Creating directory: {}'.format(dirpath))
        try:
            os.mkdir(dirpath)
        except EnvironmentError as ex:
            raise CreateError(path=dirpath, ex=ex)
        return dirpath

    return None


def debug(*args, **kwargs):
    """ Print a message only if DEBUG is truthy. """
    if not (DEBUG and args):
        return None

    # Include parent class name when given.
    parent = kwargs.get('parent', None)
    with suppress(KeyError):
        kwargs.pop('parent')

    # Go back more than once when given.
    backlevel = kwargs.get('back', 1)
    with suppress(KeyError):
        kwargs.pop('back')

    frame = inspect.currentframe()
    # Go back a number of frames (usually 1).
    while backlevel > 0:
        frame = frame.f_back
        backlevel -= 1
    fname = os.path.split(frame.f_code.co_filename)[-1]
    lineno = frame.f_lineno
    if parent:
        func = '{}.{}'.format(parent.__class__.__name__, frame.f_code.co_name)
    else:
        func = frame.f_code.co_name

    # Patch args to stay compatible with print().
    pargs = list(args)

    lineinfo = '{}:{} {}(): '.format(fname, lineno, func).ljust(40)
    pargs[0] = ''.join((lineinfo, pargs[0]))
    print(*pargs, **kwargs)


def django_src_path(relpath):
    """ Return the full path to a django installation's sub dir.
        On error, prints a message and returns None.
    """
    srcpath = os.path.join(
        django_init.django_path,
        relpath)
    if not os.path.exists(srcpath):
        print_err('Missing django path: {}'.format(
            srcpath
        ))
        return None
    return srcpath


def is_modified(srcfile, destfile):
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
        if os.path.isfile(destfile):
            dstmod = os.path.getmtime(destfile)
        else:
            # Destination doesn't exit yet.
            return True
    except Exception as ex:
        print('\nUnable to stat file: {}'.format(destfile, ex))
        return False

    if srcmod > dstmod:
        # Source file is newer than the destination file
        return True

    # destination file is newer than the source file
    return False


def print_copy_err(srcfile, destfile, lbl=None):
    """ Print an error message pertaining to failed file copies. """
    lbl = ' {}'.format(lbl) if lbl else ''
    print_err('\n'.join((
        'Failed to copy{ftype} file:',
        '    Source: {src}',
        '     Dest.: {dest}'
    )).format(
        ftype=lbl,
        src=srcfile,
        dest=destfile
    ))


def print_err(*args, **kwargs):
    """ Wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def warn_live():
    """ Print a helpful warning if the live site may be interrupted.
        Offer the user a chance to cancel the operation.
    """
    print_err('\nYou are working on the ** LIVE SITE ** !')
    print_err('Continuing will restart the server...')
    warn_response = input('\n    Continue anyway? (y|n): ')
    if not warn_response.lower().startswith('y'):
        print_err('\nCancelling, goodbye.')
        return False
    return True


class CopyError(EnvironmentError):
    def __init__(self, src=None, dest=None, ex=None):
        self.src = str(src)
        self.dest = str(dest)
        self.ex = ex

    def __str__(self):
        lines = ['Failed to copy file:']
        if self.src:
            lines.append('    Source: {s.src}')
        if self.dest:
            lines.append('     Dest.: {s.dest}')
        if self.ex:
            lines.append('  {s.ex}')
        return '\n'.join(lines).format(s=self)


class CreateError(EnvironmentError):
    def __init__(self, path=None, ex=None):
        self.path = str(path)
        self.ex = ex

    def __str__(self):
        return '\n'.join((
            'Failed to create directory: {s.path}',
            '  {s.ex}'
        )).format(s=self)


# START OF SCRIPT ------------------------------------------------------------
if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    except (CopyError, CreateError) as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser Cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('Broken pipe.')
        mainret = 3
    sys.exit(mainret)
