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
from functools import wraps

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
    print(
        '\nMissing django_init.py!:\n{}'.format(eximp),
        file=sys.stderr)
    sys.exit(1)
except Exception as ex:
    print(
        '\nError initializing django environment!:\n{}'.format(ex),
        file=sys.stderr)
    sys.exit(1)

# Get Django Settings and Cache to work with.
# ...must be imported after django_init!
from django.conf import settings     # noqa
from django.core.cache import cache  # noqa

USAGESTR = """{version}

    Usage:
        wprefresh.py -h | -v
        wprefresh.py -r [-l] [-D]
        wprefresh.py [-c] [-d] [-k] [-l] ([-C] | [-R]) [-t] [-D]

    Options:
        -C,--nocollect       : Skip static collection.
        -c,--clearcache      : Clear Django's cache for the WP site.
        -D,--debug           : Prints extra info (not much right now).
        -d,--django          : Refresh django admin css/js/etc. also.
        -h,--help            : Show this message.
        -l,--live            : Suppress warning about live site.
        -R,--norestart       : Skip apache restart.
        -r,--restart         : Just restart the server, nothing else.
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

# If any warnings are available after all commands run, they will be printed
# to stderr. This is so they don't get lost in the mix.
WARNINGS = set()


def main(argd):
    global DEBUG
    DEBUG = argd['--debug']
    # if test is passed no warning is given before restarting the server.
    test = (
        settings.SERVER_LOCATION == 'local' or
        settings.SITE_VERSION.lower() != 'main site'
    )
    warn = False if test else (not (argd['--live'] or argd['--norestart']))

    # Show warning if needed..
    if warn and (not warn_live()):
        return 0

    # Just restart
    if argd['--restart']:
        cmd_apache_restart()
        return 0

    if argd['--django']:
        # Move django css/js/etc. to /static/admin
        cmd_collect_django_admin_files()
    if argd['--admintemplates']:
        # Move django template to wp_main/templates/admin
        cmd_collect_django_admin_templates()

    # Run collect static
    if not argd['--nocollect']:
        cmd_collect_static()

    # Run apache restart
    if not argd['--norestart']:
        cmd_apache_restart()

    if argd['--clearcache']:
        cmd_clear_cache()

    return 0


def check_call(func):
    """ Convert a simple boolean-returning function into a "checked call",
        where if the command returns a Falsey value a CommandError is raised.
        This also catches CopyError and CreateError, converting them to
        CommandError (building a better error message).
        These errors are caught above main(), and will cause a program exit.
    """
    @wraps(func)
    def run_func(*args, **kwargs):
        try:
            cmdreturn = func(*args, **kwargs)
        except (CopyError, CreateError) as ex:
            # Instead of just CopyError, tell the user which command did it.
            raise CommandError(
                name=func.__name__,
                msg=str(ex)
            )
        else:
            if not cmdreturn:
                raise CommandError(
                    name=func.__name__,
                    msg='Return value was: {}'.format(cmdreturn)
                )

        return True

    return run_func


@check_call
def cmd_apache_restart():
    """ Restart the apache server """
    # apache restart locations.
    remote_apache_path = os.path.join(settings.BASE_PARENT, 'apache2', 'bin')
    if os.path.isdir(remote_apache_path):
        # Remote: `../apache2/bin/restart`
        restartcmd = '{}/restart'.format(remote_apache_path)
        if not os.path.exists(restartcmd):
            raise CommandError(
                'cmd_apache_restart',
                'Apache command not found: {}'.format(restartcmd)
            )
    else:
        # Local: `sudo apache2 restart`
        local_apachecmd = '/etc/init.d/apache2'
        restartcmd = ' '.join(('sudo', local_apachecmd, 'restart'))
        if not os.path.exists(local_apachecmd):
            raise CommandError(
                name='cmd_apache_restart',
                msg='Apache command not found: {}'.format(local_apachecmd)
            )

    print('\nRestarting apache... ({})'.format(restartcmd))
    try:
        callret = os.system(restartcmd)
        cmdreturn = (callret == 0)
    except Exception as ex:
        raise CommandError(
            name='cmd_apache_restart',
            msg='Unable to restart apache:\n{}'.format(ex)
        )

    return cmdreturn


@check_call
def cmd_clear_cache():
    """ Clear Django's cache. """

    try:
        print('\nClearing the cache...')
        cache.clear()
    except Exception as ex:
        raise CommandError(
            name='cmd_clear_cache',
            msg='Error clearing the cache:\n{}'.format(ex)
        )

    print('\nCache was cleared.')
    return True


@check_call
def cmd_collect_django_admin_templates():
    """ Move admin templates to proper dir for use.
        Possibly raises CopyError or CreateError.
    """
    # admin css dirs (source, target)
    admin_dest = os.path.join(
        django_init.project_dir,
        'wp_main/templates/admin'
    )
    admin_src = django_src_path('contrib/admin/templates/admin')

    change_files = ('admin/base.html', 'change_list_results.html',)

    print('\nCopying admin templates from: {}'.format(admin_src))
    copied_files = copy_tree(admin_src, admin_dest)
    for copiedfile in copied_files:
        for changefile in change_files:
            if copiedfile.endswith(changefile):
                warning_add('Must be edited again: {}'.format(copiedfile))
    return True


@check_call
def cmd_collect_django_admin_files():
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


@check_call
def cmd_collect_static():
    """ Run manage.py collectstatic """
    manage_py = os.path.join(settings.BASE_DIR, 'manage.py')

    if not os.path.isfile(manage_py):
        print_err('manage.py is missing!: {}'.format(manage_py))
        return False

    # No user input when running wprefresh.
    collect_cmd = ['python3', manage_py, 'collectstatic', '--noinput']
    # Add all ignored patterns.
    for globpat in STATIC_IGNORE:
        collect_cmd.extend(('--ignore', globpat))

    cmdstr = ' '.join(collect_cmd)
    print('Running collectstatic: {}'.format(cmdstr))
    callret = os.system(cmdstr)

    return (callret == 0)


def copy_file(srcfile, destfile, force=False):
    """ Copies a single file if it has been modified, or `force` is used.
        Returns the dest. name on copies, and None for non-modified files.
        Raises a CopyError on failure.
    """

    if force or is_modified(srcfile, destfile):
        cp_cmd = ['cp', '-r', srcfile, destfile]
        callret = os.system(' '.join(cp_cmd))
        if callret == 0:
            print('  Copied {}\n    {}'.format(srcfile, destfile))
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
        debug('  Creating directory: {}'.format(dirpath))
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


def warning_add(s):
    """ Add a warning to be printed when the program terminates. """
    global WARNINGS
    WARNINGS.add(s)


def warnings():
    """ Print any warnings that were collected while running. """
    if not WARNINGS:
        return False
    print_err('\nWarnings ({}):'.format(len(WARNINGS)))
    for warnmsg in WARNINGS:
        print_err('    {}'.format(warnmsg))
    return True


class CommandError(Exception):
    def __init__(self, name=None, msg=None):
        self.name = name or 'Unknown Function'
        self.msg = msg

    def __str__(self):
        lines = ['WpRefresh command failed: {}']
        if self.msg:
            lines.append('  {}'.format(self.msg))
        return '\n'.join(lines)


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
    except (CommandError, CopyError, CreateError) as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser Cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('Broken pipe.')
        mainret = 3
    # Print any warnings that were generated.
    warnings()
    sys.exit(mainret)
