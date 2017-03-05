#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" wpstatic.py
    ...some tools to work with static files for Welborn Prod.
    -Christopher Welborn 08-30-2014
"""

import os
import re
import sys
from collections import defaultdict

from colr import (
    Colr as C,
    auto_disable as colr_auto_disable,
    docopt,
)
from fmtblock import FormatBlock
from printdebug import DebugColrPrinter
try:
    import django_init
    if not django_init.init_django():
        sys.exit(1)
except ImportError as eximp:
    print(
        'Unable to import django_init.py, this won\'t work.',
        file=sys.stderr
    )
    print('Error: {}'.format(eximp), file=sys.stderr)
    sys.exit(1)

# Import django stuff.
from django.conf import settings

debugprinter = DebugColrPrinter()
debugprinter.disable()
debug = debugprinter.debug

colr_auto_disable()

NAME = 'WpStatic'
VERSION = '0.2.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-i pat] [-D]
        {script} (-a [-C] | -d [-m]) [-c] [-i pat] [-D]

    Options:
        -a,--analyze          : Analyze static files dirs, don't do anything.
                                This is the default action with no arguments.
        -C,--compiled         : Show compiled files that were accounted for.
        -c,--clean            : Remove stray collected files and duplicate/old
                                versioned files.
        -d,--dupeversions     : Find duplicate files, with different versions.
        -D,--debug            : Print some debugging info while running.
        -h,--help             : Show this help message.
        -i pat, --ignore pat  : Ignore directories matching this pattern.
        -m,--min              : Show min files, even though they are not
                                true duplicates.
        -v,--version          : Show version.

    * With no arguments the default action is --analyze.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

IGNORE_COLLECTED = set([
    'debug_toolbar',
    'django_extensions',
    'media',
])

IGNORE_DEV = set([
    # Ignore sass master files.
    'sass/_[\w\-\.\d]+\.scss',
    # Ignore browserify 'in' files.
    'js/_in[\w\-\.\d]+\.js',
])

IGNOREPAT = None
IGNOREPAT_DEV = None

# Patterns for collected files that will never have a dev version.
NEVERDEV = [
    '/admin/.+\.[\w]{2,3}',
    '/admin/.+/LICENSE',
]
IGNORE_COLLECTED.update(NEVERDEV)

# Directories where development files live. They should be collected.
# TODO: Configurable dev dirs (config file based).
DEVDIRS = ('static', 'built')

# Can be set with -D,--debug.
DEBUG = False

# Set in main() if available.
TERMWIDTH = 80
TERMHEIGHT = 25


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    global DEBUG, IGNORE_COLLECTED, IGNOREPAT, IGNOREPAT_DEV
    global TERMWIDTH, TERMHEIGHT
    DEBUG = argd['--debug']
    if DEBUG:
        debugprinter.enable()
    TERMWIDTH, TERMHEIGHT = get_terminal_size()

    ignorepat = try_re(argd['--ignore'])
    if ignorepat is not None:
        IGNORE_COLLECTED.add(argd['--ignore'])
        IGNORE_DEV.add(argd['--ignore'])

    IGNOREPAT = re.compile('/?(({}))'.format(
        ')|('.join(IGNORE_COLLECTED)
    ))
    print('Gathering collected files...')
    collected = get_collected()

    IGNOREPAT_DEV = re.compile('/?(({}))'.format(
        ')|('.join(IGNORE_DEV)
    ))
    print('Gathering development files...')
    development = get_development()

    if argd['--dupeversions']:
        # TODO: Clean duplicate/old versions.
        return do_duplicate_vers(
            collected,
            development,
            min_files=argd['--min'],
            clean=argd['--clean'],
        )

    # Analyze the dirs (default action).
    return do_analyze(
        collected,
        development,
        clean=argd['--clean'],
        show_compiled=argd['--compiled'],
    )


def clean_files(fileinfos):
    """ Remove files in an iterable of FileInfos.
        Returns the number of files removed.
    """
    if not fileinfos:
        return 0
    filelen = len(fileinfos)
    plural = 'file' if filelen == 1 else 'files'
    msg = 'This will remove {} {}!\n\nContinue?'.format(filelen, plural)
    if not confirm(msg):
        raise UserCancelled()

    total = 0
    for fi in fileinfos:
        try:
            os.remove(fi.fullpath)
        except EnvironmentError as ex:
            print_err('Unable to remove: {}\n  {}'.format(
                fi.fullpath,
                ex
            ))
        else:
            total += 1
    return total


def color_num(n):
    """ Colrize a number. This function is used for consistency. """
    return C(n, fore='blue', style='bright')


def confirm(s, default=False):
    """ Confirm a yes/no question. """

    defaultstr = 'Y/n' if default else 'y/N'
    s = '{} ({}): '.format(s, defaultstr)
    answer = input(s).strip().lower()
    if not answer:
        return default
    return answer[0].startswith('y')


def do_analyze(collected, development, clean=False, show_compiled=False):
    """ Analyze the difference between collected/development files. """
    colnodev = collected.difference(development)
    devnocol = development.difference(collected)
    trimmed = trim_compiled_files(
        collected,
        colnodev,
        development,
        devnocol
    )
    if not (colnodev or devnocol):
        print('\nThere are no stray files in collected/development.')
        if trimmed:
            print('Compiled files ignored: {}'.format(len(trimmed)))
            if show_compiled:
                print(
                    '\n'.join(
                        fi.to_str(color=True, indent='    ')
                        for fi in sorted(trimmed, key=lambda f: f.relpath)
                    )
                )
        return 0

    errs = 0
    if colnodev:
        print('\nCollected files not in development:')
        print(
            '\n'.join(
                fi.to_str(color=True, indent='    ')
                for fi in sorted(colnodev, key=lambda f: f.relpath)
            )
        )
        colnodevlen = len(colnodev)
        fileplural = 'file' if colnodevlen == 1 else 'files'
        print('\nFound {} {} not in development.'.format(
            colnodevlen,
            fileplural))
        if clean:
            removedcnt = clean_files(colnodev)
            print('Files removed: {} of {}'.format(removedcnt, colnodevlen))
            # Error status is number of files that weren't cleaned.
            errs += len(colnodev) - removedcnt
        else:
            errs += 1
    else:
        print('\nAll collected files are from development.')

    if devnocol:
        print('\nDevelopment files not in collected:')
        print(
            '\n    '.join(
                fi.to_str(color=True, indent='    ')
                for fi in sorted(devnocol, key=lambda s: s.relpath)
            )
        )
        devnocollen = len(devnocol)
        fileplural = 'file' if devnocollen == 1 else 'files'
        print(
            '\nFound {} {} not in collected.'.format(
                devnocollen,
                fileplural
            )
        )
        errs += 1
    else:
        print('\nAll development files have been collected.')

    return errs


def do_duplicate_vers(collected, development, min_files=False, clean=False):
    """ Search for duplicate versioned files. """
    if clean:
        raise NotImplementedError('No --clean yet. It could be harmful.')

    dupes = print_duplicate_vers(
        find_duplicate_vers(collected),
        label='collected',
        min_files=min_files,
    )
    dupes += print_duplicate_vers(
        find_duplicate_vers(development),
        label='development',
        min_files=min_files,
    )

    print('\nTotal duplicate versioned files: {}'.format(color_num(dupes)))
    return dupes


def find_duplicate_vers(fileinfos):
    """ Finds only FileInfos that have multiple versioned files.
        Returns a dict of {basename: [FileInfo, ..]}.
    """
    return {
        basename: verlst
        for basename, verlst in get_versioned_files(fileinfos).items()
        if len(verlst) > 1
    }


def get_collected():
    """ Gather files from the collected static dir. """
    collected = set()
    for root, dirs, files in os.walk(settings.STATIC_ROOT):
        dirname = os.path.split(root)[-1]
        if dirname.startswith('.'):
            continue
        for dirname in dirs:
            if dirname.startswith('.'):
                dirs.remove(dirname)
        if 'static_server' in settings.STATIC_ROOT:
            splitter = 'static_server'
        else:
            splitter = 'static'

        for f in files:
            fullpath = os.path.join(root, f)
            relativeparts = fullpath.split(splitter)[1:]
            relpath = splitter.join(relativeparts)
            if IGNOREPAT.match(relpath):
                continue
            collected.add(FileInfo(fullpath, relpath))
    return collected


def get_development(devdirs=None):
    """ Gather files from the development static dirs. """
    development = set()
    devdirs = devdirs or DEVDIRS
    for root, dirs, files in os.walk(settings.BASE_DIR):
        dirname = os.path.split(root)[-1]
        if dirname.startswith('.'):
            continue
        for dirname in dirs:
            if dirname.startswith('.'):
                dirs.remove(dirname)

        if not str_contains(root, devdirs):
            continue

        for f in files:
            fullpath = os.path.join(root, f)
            relativepath = get_rel_path_at(fullpath, devdirs)
            if (
                    IGNOREPAT.match(relativepath) or
                    IGNOREPAT_DEV.match(relativepath)):
                continue
            development.add(FileInfo(fullpath, relativepath))
    return development


def get_rel_path_at(fullpath, subdirs):
    for subdir in subdirs:
        if subdir not in fullpath:
            continue
        relativeparts = fullpath.split(subdir)[1:]
        return subdir.join(relativeparts)


def get_terminal_size(default=(80, 25)):
    """ Return terminal (width, height) """
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except KeyError:
            return default
    return int(cr[1]), int(cr[0])


def get_versioned_files(fileinfos):
    """ Find versioned files in a set of FileInfos.
        Returns a dict of {basename: [FileInfo, ..]}.
    """
    versinfo = defaultdict(list)
    for fi in fileinfos:
        if fi.version is not None:
            versinfo[fi.shortbase].append(fi)

    return versinfo


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def print_duplicate_vers(verinfo, label=None, min_files=False):
    """ Prints any duplicate versioned files found with find_duplicate_vers.
        Returns the number of duplicated basenames found.
    """
    if not verinfo:
        print('    No duplicate versioned files.')
        return 0
    verfileinfos = []
    onlymins = 0
    for basename in sorted(verinfo):
        verfileinfo = VersionedFileInfo(basename, verinfo[basename])
        if (not min_files) and verfileinfo.only_min:
            # This file has one "duplicate" version, but it's just a .min file
            onlymins += 1
            continue
        verfileinfos.append(verfileinfo)
    if onlymins:
        minstr = ' {}'.format(
            color_num(onlymins).join(
                C('+', 'lightblue'),
                C(' false-positive .min files', 'green')
            ).join('(', ')', style='bright')
        )
    else:
        minstr = ''
    verlen = len(verinfo) - onlymins
    lblstr = 'Duplicate versioned files{lbl}, {total}{mins}:'.format(
        lbl=' in {}'.format(C(label, 'lightblue')) if label else '',
        total=color_num(verlen),
        mins=minstr,
    )
    print('\n{}'.format(lblstr))
    if verfileinfos:
        print('\n'.join(str(verfile) for verfile in verfileinfos))
    else:
        print(C('    None', 'green', style='bright'))
    return verlen


def str_contains(s, strlst):
    return any(x in s for x in strlst)


def trim_compiled_files(collected, colnodev, development, devnocol):
    """ Remove FileInfos from the difference sets if they have a compiled
        version found in the other.
        Returns a set of all removed FileInfos.
    """
    col_rel_paths = set((fi.relpath for fi in collected))
    trimmed = set()
    for devfi in list(devnocol):
        if not devfi.relcompiledpath:
            continue
        # Remove from devnocol if the compiled version is in collected.
        if devfi.relcompiledpath in col_rel_paths:
            trimmed.add(devfi)
            devnocol.remove(devfi)
            if devfi in colnodev:
                colnodev.remove(devfi)

    return trimmed


def try_re(s):
    """ Try compiling a regex pattern. Exit with a message on failure.
        If None is passed, no error is given and None is returned.
    """
    if s is None:
        return None

    try:
        pat = re.compile(s)
    except re.error as ex:
        print('\nInvalid pattern: {}\n  {}'.format(s, ex))
        sys.exit(1)
    return pat


class FileInfo(object):
    __slots__ = (
        'basename',
        'extension',
        'filename',
        'fulldir',
        'fullpath',
        'reldir',
        'relpath',
        'shortbase',
        'version',
        'relcompiledpath',
    )

    def __init__(self, fullpath, relpath):
        self.fullpath = fullpath
        self.fulldir, self.filename = os.path.split(self.fullpath)
        self.relpath = relpath.strip()
        self.reldir = os.path.split(relpath)[0]
        self.basename, self.extension = os.path.splitext(self.filename)
        verpat = re.compile('\d+\.\d+\.\d+')
        vermatch = verpat.search(self.basename)
        if vermatch is None:
            self.version = None
            self.shortbase = self.basename
        else:
            self.version = vermatch.group()
            basepat = re.compile('(.+(!?-)+)\d')
            basematch = basepat.search(self.basename)
            if basematch is None:
                self.shortbase = self.basename
            else:
                self.shortbase = basematch.groups()[0].rstrip('-')
        self.relcompiledpath = self.get_compiled_path()

    def __eq__(self, other):
        return self.relpath == getattr(other, 'relpath', object())

    def __str__(self):
        return self.to_str(color=False)

    def __hash__(self):
        """ In a set, FileInfo's are equal if their relative path is equal.
        """
        return hash(self.relpath)

    def get_compiled_path(self):
        """ Get the relative file path for this file, after compilation.
            If this file does not get compiled, then '' is returned.
        """
        compiled_exts = {
            '.js': {'ext': '.min.js', 'origdir': 'js', 'cmpdir': 'js'},
            '.scss': {'ext': '.min.css', 'origdir': 'sass', 'cmpdir': 'css'},
        }
        otherext = os.path.splitext(self.basename)[-1]
        if otherext == '.min':
            return None
        compiled_info = compiled_exts.get(self.extension, None)
        if compiled_info is None:
            # Not a compiled file.
            return ''
        reldir = os.path.split(self.relpath)[0]
        compiledname = '{}{}'.format(self.basename, compiled_info['ext'])
        if compiled_info['origdir'] != compiled_info['cmpdir']:
            # Directory changes too.
            origindex = reldir.rfind(compiled_info['origdir'])
            cmplen = len(compiled_info['cmpdir'])

            reldir = ''.join((
                reldir[:origindex],
                compiled_info['cmpdir'],
                reldir[origindex + cmplen + 1:]
            ))
        return os.path.join(reldir, compiledname)

    def to_str(self, color=False, indent=None):
        """ Return a stringified version of this FileInfo, with optional
            color.
        """
        relpath = self.relpath.ljust(45)
        if color:
            relpath = C(relpath, 'cyan')
        if 'static_server' in settings.STATIC_ROOT:
            repl = '/static_server'
        else:
            repl = '/static'
        fullpath = (
            self.fullpath
            .replace(settings.BASE_DIR, '')
            .replace(settings.STATIC_ROOT, repl)
        )
        if color:
            fullpath = C(fullpath, 'blue')

        compiled = self.relcompiledpath or ''
        if compiled:
            if color:
                compiled = C('  ').join(
                    C('⮕ ', 'lightgreen'),
                    C(compiled, 'green'),
                )
            else:
                compiled = '⮕ {}'.format(compiled)

        return '{indent}{rel} - ..{full}{compiled}'.format(
            indent=str(indent) if indent else '',
            rel=relpath,
            full=fullpath,
            compiled='' if not compiled else (
                '\n{}{}{}'.format(
                    str(indent) if indent else '',
                    ' ' * 46,
                    compiled,
                )
            )
        )


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {}'.format(self.msg)
        return 'Invalid argument!'


class UserCancelled(KeyboardInterrupt):
    def __init__(self, msg=None):
        self.msg = msg or 'User Cancelled'

    def __str__(self):
        return str(self.msg)


class VersionedFileInfo(object):
    """ Holds info about a single file with multiple versions. """
    __slots__ = (
        '_versions',
        'basename',
        'only_min',
        'versions',
    )
    # Basename indent level.
    basename_rjust = 25

    def __init__(self, basename, versions):
        self.basename = basename
        self._versions = versions
        self.versions = self._remove_min_files(versions)
        # If only one .version is left, then it's not really a duplicate.
        # It only has a min file, with the same version.
        self.only_min = (len(self.versions) == 1)

    def __str__(self):
        # Amount to indent version info, plus 2 for ': '.
        verindent = ' ' * (self.basename_rjust + 2)
        # Width, not counting indent, allowed for relative paths.
        filenamewidth = (TERMWIDTH + len(verindent)) - self.basename_rjust
        verstrlines = []
        for fi in self.versions:
            pathfmt = C(fi.relpath, 'cyan')
            minfile = self.get_min_file(fi.relpath)
            if minfile:
                pathfmt = C(' ').join(
                    pathfmt,
                    C('{} {}'.format(
                        C('and', 'cyan'),
                        C(minfile, 'green'),
                    )).join('(', ')', style='bright')
                )
            verstrlines.append(str(pathfmt))
        verstr = FormatBlock(
            '\n'.join(verstrlines)
        ).format(
            prepend=verindent,
            newlines=True,
            strip_first=True,
            width=filenamewidth,
        )
        return '{bname:>{bnamerjust}}: {verstr}'.format(
            bname=self.basename,
            bnamerjust=self.basename_rjust,
            verstr=verstr
        )

    @staticmethod
    def _remove_min_files(fis):
        """ Remove any FileInfos from a list that are minified files. """
        return [
            fi
            for fi in fis
            if '.min.' not in fi.relpath
        ]

    def get_min_file(self, relpath):
        """ Return any .min file that is related to this relpath.
            Returns None if one can't be found.
        """
        base, ext = os.path.splitext(relpath)
        minfile = '{}.min{}'.format(base, ext)
        for fi in self._versions:
            if fi.relpath == minfile:
                return minfile
        return None

    def has_min_files(self):
        return len(self._versions) > len(self.versions)


if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR, script=SCRIPT))
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\nBroken pipe, input/output was interrupted.\n')
        mainret = 3
    sys.exit(mainret)
