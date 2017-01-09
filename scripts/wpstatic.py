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
VERSION = '0.1.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-i pat] [-D]
        {script} (-a | -c | -d [-m]) [-i pat] [-D]

    Options:
        -a,--analyze          : Analyze static files dirs, don't do anything.
                                This is the default action with no arguments.
        -c,--clean            : Analyze and clean the static files dir.
        -d,--dupeversions     : Find duplicate files, with different versions.
        -D,--debug            : Print some debugging info while running.
        -h,--help             : Show this help message.
        -i pat, --ignore pat  : Ignore directories matching this pattern.
        -m,--min              : Show min files, even though they are not
                                true duplicates.
        -v,--version          : Show version.

    * With no arguments the default action is --analyze.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

# TODO: Account for transformations: file.scss -> file.min.css
IGNORECOLLECTED = [
    # 'admin',
    'debug_toolbar',
    'django_extensions',
    'media',
]

# TODO: Ignore _welbornprod (master sass files), _in-blah.js (browserify).
IGNOREDPAT = None

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
    global DEBUG, IGNORECOLLECTED, IGNOREDPAT, TERMWIDTH, TERMHEIGHT
    DEBUG = argd['--debug']
    if DEBUG:
        debugprinter.enable()
    TERMWIDTH, TERMHEIGHT = get_terminal_size()

    if argd['--clean']:
        raise NotImplementedError('No --clean yet. It could be harmful.')

    ignorepat = try_re(argd['--ignore'])
    if ignorepat is not None:
        IGNORECOLLECTED.append(argd['--ignore'])

    IGNOREDPAT = re.compile('/?(({}))'.format(
        ')|('.join(IGNORECOLLECTED)
    ))
    print('Gathering collected files...')
    collected = get_collected()

    print('Gathering development files...')
    development = get_development()

    if argd['--dupeversions']:
        return do_duplicate_vers(
            collected,
            development,
            min_files=argd['--min']
        )

    # Analyze the dirs (default action).
    return do_analyze(collected, development)


def color_num(n):
    """ Colrize a number. This function is used for consistency. """
    return C(n, fore='blue', style='bright')


def do_analyze(collected, development):
    """ Analyze the difference between collected/development files. """
    colnodev = collected.difference(development)
    devnocol = development.difference(collected)
    if not (colnodev or devnocol):
        print('\nThere are no stray files in collected/development.')
        return 0

    errs = 0
    if colnodev:
        print('\nCollected files not in development:')
        print(
            '    {}'.format(
                '\n    '.join(
                    str(fi)
                    for fi in sorted(colnodev, key=lambda s: s.relpath)
                )
            )
        )
        colnodevlen = len(colnodev)
        fileplural = 'file' if colnodevlen == 1 else 'files'
        print('\nFound {} {} not in development.'.format(
            colnodevlen,
            fileplural))
        errs += 1
    else:
        print('\nAll collected files are from development.')

    if devnocol:
        print('\nDevelopment files not in collected:')
        print(
            '    {}'.format(
                '\n    '.join(
                    str(fi)
                    for fi in sorted(devnocol, key=lambda s: s.relpath)
                )
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


def do_duplicate_vers(collected, development, min_files=False):
    """ Search for duplicate versioned files. """
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
        for f in files:
            fullpath = os.path.join(root, f)
            relativeparts = fullpath.split('static')[1:]
            relpath = 'static'.join(relativeparts)
            if IGNOREDPAT.match(relpath):
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
            if IGNOREDPAT.match(relativepath):
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
    )

    def __init__(self, fullpath, relpath):
        self.fullpath = fullpath
        self.fulldir, self.filename = os.path.split(self.fullpath)
        self.relpath = relpath
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

    def __eq__(self, other):
        return self.relpath == getattr(other, 'relpath', object())

    def __str__(self):
        return '{rel:<45} - {full}'.format(
            rel=self.relpath,
            full=(
                self.fullpath
                .replace(settings.BASE_DIR, '..')
                .replace(settings.STATIC_ROOT, '../static')
            ),
        )

    def __hash__(self):
        """ In a set, FileInfo's are equal if their relative path is equal.
        """
        return hash(self.relpath)


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
            pathfmt = C(fi.relpath.strip(), 'cyan')
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
    mainret = main(docopt(USAGESTR, version=VERSIONSTR, script=SCRIPT))
    sys.exit(mainret)
