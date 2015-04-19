#!/usr/bin/env python3
# -*- coding: utf-8 -*-

usage_str = """findexe.py

    Finds executables by looking in all popular ../bin directories.

    Usage:
        findexe.py <searchterm> [-a] [-e dirs] [-s] [-q]
        findexe.py -d

    Options:
        -h,--help                   : Show this message.
        <searchterm>                : Name, or part of a name to search for.
        -a,--argstyle               : Output is formatted in argument-style so
                                      it can be used with another command like:
                                      stat `findexe ls -a`
                                      Output is either nothing ('') with
                                      return code 1,
                                      or 'file1 file2 file3' with return
                                      code 0.
        -d,--dirs                   : List the known executable directories.
        -e <dirs>,--exclude <dirs>  : Directories to exclude,
                                      separated by ',' or ':'.
        -s,--sort                   : Sort results.
                                      Results aren't shown as they're found.
        -q,--quote                  : Quote paths when argstyle is used.
"""

__VERSION__ = '1.1.0'
from datetime import datetime
import os
import re
import sys
# A great module for parsing args based on the usage string.
from docopt import docopt

# Usual directories for executables...
PATH = set(os.environ.get('PATH', '').split(':'))
# Some of these may not be in $PATH, we will add the ones that are missing.
DIRS = set([
    '/usr/local/bin',
    '/usr/local/sbin',
    '/usr/bin',
    '/usr/sbin',
    '/bin',
    '/sbin',
    os.path.expanduser('~/bin'),
    os.path.expanduser('~/local/bin'),
    os.path.expanduser('~/.local/bin'),
])
# This is the final list of dirs we will be working with.
# PATH is kept separate for later (we can see which dirs are not in PATH)
DIRS.update(PATH)


def main(argd):
    """ main entry point, expects arguments from docopt. """

    if argd['--dirs']:
        return print_dirs()

    # Get regex pattern to sarch with
    try:
        repat = re.compile(argd['<searchterm>'])
    except:
        print('\nInvalid search term given!\n')
        return 1

    # Only search valid/existing directories in DIRS
    dirs = parse_dirs(excludedirs=argd['--exclude'])
    # Only print header if --argstyle is not used.
    if not argd['--argstyle']:
        headerfmt = '\nSearching {} directories for: {}\n'
        print(headerfmt.format(len(dirs), argd['<searchterm>']))

    # Results are printed as they are found without -a or -s.
    printer = None if (argd['--argstyle'] or argd['--sort']) else print
    # Start searching
    results = search_dirs(dirs, repat, reporter=printer)

    if argd['--argstyle'] or argd['--sort']:
        if argd['--sort']:
            argstyle_exes = sorted(results['exes'])
        else:
            argstyle_exes = results['exes']

        # argstyle output means ' ' separated filepaths.
        # sorted output means \n separated filepaths.
        joiner = ' ' if argd['--argstyle'] else '\n'

        fmt = quote if argd['--quote'] else (lambda s: s)
        print(joiner.join(fmt(p) for p in argstyle_exes))

        if argd['--argstyle']:
            # Nothing else is needed for argstyle.
            return 0 if argstyle_exes else 1

    # Print footer for non-argstyle output
    if results['exes']:
        foundfiles = len(results['exes'])
        founddirs = len(results['dirs'])
        print(('\nFound {} files in '
               '{} directories.').format(foundfiles, founddirs))
    else:
        print('\nNo files found matching: {}'.format(argd['<searchterm>']))
    # show time, trim to acceptable decimal point
    print('{:0.2f}s'.format(results['duration']))
    return 0


def parse_excludes(excludestr):
    """ Turns a separated list of dirs into an actual list.
        Acceptable separators are: ,;:
        example:
            excluded = parse_excludes('/usr/bin,/usr/local/bin')
            # returns ['/usr/bin', '/usr/local/bin']
    """
    if not excludestr:
        return None

    excludestr = excludestr.replace(':', ',').replace(';', ',')
    return excludestr.split(',')


def parse_dirs(excludedirs=None):
    """ Checks all dirs, and only returns the valid existing dirs. """

    gooddirs = []
    excluded = parse_excludes(excludedirs)
    for sdir in DIRS:
        if os.path.isdir(sdir):
            if not (excluded and (sdir in excluded)):
                gooddirs.append(sdir)
    if not gooddirs:
        print('\nNo valid directories found!\n')
        sys.exit(1)

    return sorted(gooddirs)


def print_dirs():
    """ Prints the directories that will be searched. """
    dirlen = len(DIRS)
    dirplural = 'directory' if (dirlen == 1) else 'directories'
    notinpath = []
    print('Using {} {}:'.format(dirlen, dirplural))
    for usingdir in sorted(DIRS):
        if usingdir in PATH:
            marker = ' '
        else:
            marker = '*'
            notinpath.append(usingdir)
        print('    {}{}'.format(marker, usingdir))

    if notinpath:
        if len(notinpath) == 1:
            thisplural = 'This known directory'
            isplural = 'is'
        else:
            thisplural = 'These known directories'
            isplural = 'are'
        msgfmt = (
            '\n* {this} {iss} being searched, '
            'but {iss} not found in $PATH.')
        print(msgfmt.format(this=thisplural, iss=isplural))
    else:
        print('\nAll directories are in $PATH.')

    return 0 if (dirlen > 0) else 1


def search_dirs(dirs, repat, reporter=None):
    """ Search a list of directories for executables. Returns a list of exes.
        Arguments:
            dirs      : A list of directories to search in.
            repat     : Compiled regex pattern to search with.
            reporter  : A function to report when an exe is found.
                        It is called with the path to the exe.

        Returns a dict with search info:
            {
                'dirs': set of directories where exes were found.
                'exes': set of executable paths that were found.
                'duration': total seconds it took to search.
            }
    """
    if reporter is None:
        reporter = lambda s: None

    relevantdirs = set()
    starttime = datetime.now()
    # place for --argstyle output (otherwise exes are printed as found)
    exes = set()
    try:
        for sdir in dirs:
            # walk this directory.
            for root, dirs, files in os.walk(sdir):
                for filename in files:
                    rematch = repat.search(filename)
                    if rematch:
                        # Either print the exe, or add it to argstyle output.
                        foundexe = os.path.join(root, filename)
                        exes.add(foundexe)
                        reporter(foundexe)
                        relevantdirs.add(root)

        stoptime = datetime.now()
    except (IOError, OSError) as exio:
        print('\nUnable to walk directory!\n{}'.format(exio))
        sys.exit(1)
    except Exception as ex:
        print('\nError in script!\n{}'.format(ex))
        sys.exit(1)

    duration = (stoptime - starttime).total_seconds()
    return {'dirs': relevantdirs, 'exes': exes, 'duration': duration}


def quote(s):
    """ Quote a path or string. Uses escapes and a mix of " and '. """
    escape = ('"' in s) and ("'" in s)
    char = "'" if '"' in s else '"'
    if escape:
        return '{c}{p}{c}'.format(
            c=char,
            p=s.replace(char, '\{}'.format(char))
        )
    return '{c}{p}{c}'.format(c=char, p=s)

# START OF SCRIPT
if __name__ == '__main__':
    mainret = main(docopt(usage_str, argv=sys.argv[1:]))
    sys.exit(mainret)
