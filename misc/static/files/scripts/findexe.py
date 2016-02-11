#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import os
import re
import sys
# A great module for parsing args based on the usage string.
from docopt import docopt


NAME = 'FindExe'
VERSION = '1.3.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{ver}

    Finds executables by looking in known ../bin directories, and $PATH.

    Usage:
        {script} PATTERN... ([-a] [-0] [-q]) [-e dirs]  [-s]
        {script} -d | -p

    Options:
        PATTERN...                  : Text or regex pattern.
                                      One or more names, or part of a name to
                                      search for. When multiple patterns are
                                      given, names that match any of the
                                      patterns are printed.
        -0,--null                   : Separate paths by a NULL byte when using
                                      argument-style.
        -h,--help                   : Show this message.
        -a,--argstyle               : Output is formatted in argument-style so
                                      it can be used with other commands like:
                                      stat `findexe ls -a`
                                      Output is either nothing ('') with
                                      return code 1,
                                      or 'file1 file2 file3' with return
                                      code 0.
        -d,--dirs                   : List the known executable directories.
        -e <dirs>,--exclude <dirs>  : Directories to exclude,
                                      separated by ',' or ':'.
        -p,--path                   : Print all $PATH directories.
        -s,--sort                   : Always sort results.
                                      Results aren't shown as they're found.
        -q,--quote                  : Quote paths when argstyle is used.
        -v,--version                : Show {name} version and exit.
""".format(name=NAME, ver=VERSIONSTR, script=SCRIPT)

# Usual directories for executables...
PATH = set(os.environ.get('PATH', '').split(':'))
# Some of these may not be in $PATH. We will add the ones that are missing,
# and use the existing ones (with a warning from --dirs).
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

# Any invalid path that is in PATH is saved for future reference (--dirs).
# Set by parse_dirs().
INVALIDPATHS = set()


def main(argd):
    """ main entry point, expects arguments from docopt. """

    # Only search valid/existing directories in DIRS
    dirs = parse_dirs(excludedirs=argd['--exclude'])

    if argd['--dirs']:
        return print_dirs(dirs)
    elif argd['--path']:
        return print_dirs(PATH, lbl='{} {} in PATH:', checkpath=False)

    # Get regex pattern to search with
    repat = parse_patterns(argd['PATTERN'])

    # Only print header if --argstyle is not used.
    if not argd['--argstyle']:
        headerfmt = '\nSearching {} directories for: {}\n'
        print(headerfmt.format(len(dirs), repat.pattern))

    # Results are printed as they are found without -a or -s.
    printer = _noop if (argd['--argstyle'] or argd['--sort']) else print
    # Start searching
    results = search_dirs(dirs, repat, reporter=printer)
    exitcode = 0 if results.get('exes', None) else 1

    if argd['--argstyle'] or argd['--sort']:
        exitcode = exitcode or print_results(
            results,
            sort=argd['--sort'],
            argstyle=argd['--argstyle'],
            nullstyle=argd['--null'],
            quoted=argd['--quote'],
        )
        # No further action is needed for argstyle.
        if argd['--argstyle']:
            return exitcode

    # Print footer for non-argstyle output
    if results['exes']:
        foundfiles = len(results['exes'])
        founddirs = len(results['dirs'])
        print(
            '\nFound {} files in {} directories.'.format(
                foundfiles,
                founddirs
            )
        )
    else:
        print_err('No files found matching: {}'.format(repat.pattern))
    # show time, trim to acceptable decimal point
    print('{:0.2f}s'.format(results['duration']))
    return exitcode


def _noop(*args, **kwargs):
    """ A no-op function. """
    return None


def parse_dirs(excludedirs=None):
    """ Checks all dirs, and only returns the valid existing dirs. """
    global INVALIDPATHS
    excluded = parse_excludes(excludedirs)
    gooddirs = {
        s for s in PATH
        if os.path.isdir(s)
    }
    INVALIDPATHS = PATH.difference(gooddirs)

    gooddirs = sorted(s for s in gooddirs if s not in excluded)
    if not gooddirs:
        print_err('No valid directories found!\n')
        sys.exit(1)

    return gooddirs


def parse_excludes(excludestr):
    """ Turns a separated list of dirs into an actual list.
        Acceptable separators are: ,;:
        example:
            excluded = parse_excludes('/usr/bin,/usr/local/bin')
            # returns ['/usr/bin', '/usr/local/bin']
    """
    if not excludestr:
        return []

    excludestr = excludestr.replace(':', ',').replace(';', ',')
    return excludestr.split(',')


def parse_patterns(pats, ignore_case=True):
    """ Compile several regex patterns into one long OR pattern.
        Raises InvalidArg on error, returns a compiled pattern on success.
    """
    validpats = []
    for s in pats:
        try:
            pat = re.compile(s)
        except re.error as ex:
            raise InvalidArg('Invalid pattern: {}\n{}'.format(s, ex))
        else:
            validpats.append(pat.pattern)

    finalpatstr = '|'.join('({})'.format(s) for s in validpats)
    try:
        finalpat = re.compile(
            finalpatstr,
            flags=re.IGNORECASE if ignore_case else 0
        )
    except re.error as ex:
        raise InvalidArg('Error building final pattern: {}\n{}'.format(
            finalpatstr,
            ex
        ))
    return finalpat


def print_dirs(dirs, lbl=None, checkpath=True):
    """ Prints the directories that will be searched. """
    dirlen = len(dirs)
    dirplural = 'directory' if (dirlen == 1) else 'directories'
    notinpath = []
    if lbl:
        if lbl.count('{}') == 2:
            lblfmt = lbl.format(dirlen, dirplural)
        else:
            lblfmt = lbl
    else:
        lblfmt = 'Using {} {}:'.format(dirlen, dirplural)
    print(lblfmt)

    # Print the directories.
    for usingdir in sorted(dirs):
        if usingdir in PATH:
            marker = ' '
        else:
            marker = '*'
            notinpath.append(usingdir)
        print('    {}{}'.format(marker, usingdir))

    if checkpath:
        if set(dirs) == PATH:
            # Using PATH, and PATH only.
            print('\nAll directories match what is found in PATH.')
        else:
            # Print a message about missing/invalid PATH directories.
            if notinpath:
                if len(notinpath) == 1:
                    thisplural, isplural = 'This known directory', 'is'
                else:
                    thisplural, isplural = 'These known directories', 'are'
                msg = ' '.join((
                    '\n* {this} {iss} being searched,',
                    'but {iss} not found in $PATH.'
                )).format(this=thisplural, iss=isplural)
                print_err(msg)
            else:
                print('\nAll directories are in PATH.')

            if INVALIDPATHS:
                print('\n'.join((
                    '* PATH may contain invalid directories:',
                    '    {}'.format('\n    '.join(INVALIDPATHS))
                )))
    return 0 if (dirlen > 0) else 1


def print_err(*args, **kwargs):
    """ Wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def print_results(
        results, sort=False, argstyle=False, nullstyle=False, quoted=False):
    """ Print search results with optional special formatting.
        Returns an exit status code.
    """
    exes = results.get('exes', set())
    if sort:
        exes = sorted(exes)

    # argstyle output means ' ' or '\x00' separated filepaths.
    # sorted output means \n separated filepaths.
    joiner = ('\x00' if nullstyle else ' ') if argstyle else '\n'
    fmt = quote if quoted else str
    print(joiner.join(fmt(p) for p in exes))

    return 0 if exes else 1


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
        reporter = _noop

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
        print_err('Unable to walk directory!\n{}'.format(exio))
        sys.exit(1)
    except Exception as ex:
        print_err('Error in script!\n{}'.format(ex))
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


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {}'.format(self.msg)
        return 'Invalid argument!'


# START OF SCRIPT
if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser cancelled.\n', file=sys.stderr)
        mainret = 2
    except BrokenPipeError:
        print_err(
            '\nBroken pipe, input/output was interrupted.\n',
            file=sys.stderr)
        mainret = 3
    sys.exit(mainret)
