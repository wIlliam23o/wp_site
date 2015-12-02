#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" pidname

    gets the pid of a known process name,
    or searches all processes for part of name, returns possible pids.

    Christopher Welborn
"""
from __future__ import print_function
import os
import re
import signal
import sys

from docopt import docopt

NAME = 'PidName'
__VERSION__ = '1.3.0'
VERSIONSTR = '{} v. {}'.format(NAME, __VERSION__)
SCRIPT = os.path.split(sys.argv[0])[-1]

usage_str = """{versionstr}

    Usage:
        {script} -h
        {script} -l [-e <excluded>]
        {script} (-k | -K) <name> [-e <excluded>] [-f] [-F] [-n] [-q]
        {script} <name> [-a | -A] [-f] [-n | -p] [-s]
        {script} <name> -e <excludename> [-a | -A] [-f] [-n | -p] [-s]

    Options:
        <name>                    : Known process name, or name to search for
                                    (regex allowed). You can also enter a known
                                    pid for reverse lookup.
        -h,--help                 : Show this message.
        -a,--args                 : Include command arguments in results when
                                    they trigger a match.
        -A,--ARGS                 : Always include command arguments in
                                    results.
        -e names,--exclude names  : Exclude any process names matching this
                                    regex. By default one process is always
                                    excluded, the 'pidname' process. It would
                                    list false-positives when searching process
                                    args.
        -f,--first                : Use only the first process found.
        -F,--force                : When killing processes, use SIGKILL (-9)
                                    instead of SIGTERM.
        -K,--KILL                 : Kill the processes found.
                                    (dangerous, no questions asked.)
        -k,--kill                 : Kill the processes found.
                                    (confirmation needed)
        -l,--list                 : List all running processes with arguments.
        -n,--noargsearch          : Don't search arguments for match.
        -p,--pidonly              : Like 'noargsearch', 'first', and 'short'
                                    used together.
        -q,--quiet                : When killing processes, don't print
                                    anything. This works for 'KILL', but for
                                    'kill' confirmation is always printed.
        -s,--short                : Use short output suitable for chaining with
                                    another program. multiple pids are
                                    separated by a comma.
        -v,--version              : Show {script} version.


""".format(versionstr=VERSIONSTR, script=SCRIPT)

# Python 2/3 compatibily
if sys.version_info.major < 3:
    # py2
    input = raw_input  # noqa


def main(argd):
    """ Main entry point, receives args from docopt. """

    # catch process --list command.
    if argd['--list']:
        print_allprocs(exclude=argd['--exclude'])
        return 0

    # Get name query from docopt args.
    pname = argd['<name>']

    # try compiling as a regex
    try:
        pnamepat = re.compile(pname)
    except Exception as expat:
        print_fail('Invalid name/search-term given!: '
                   '{}\n{}'.format(pname, expat))

    # Search for the pids and get some Results.
    knownpids = get_searchpid(
        pnamepat,
        exclude=argd['--exclude'],
        firstonly=argd['--first'] or argd['--pidonly'],
        noargsearch=argd['--noargsearch'])

    # Finished retrieving/searching.
    if argd['--kill'] or argd['--KILL']:
        if not knownpids:
            if not argd['--quiet']:
                print_notfound(argd['<name>'], argd['--exclude'])
            return 1

        # Kill the processes.
        returnval = kill_pids(
            knownpids,
            force=argd['--KILL'],
            sigkill=argd['--force'],
            quiet=argd['--quiet'])
    else:
        if not knownpids:
            if not argd['--pidonly']:
                print_notfound(argd['<name>'], argd['--exclude'])
            return 1

        # Print the output.
        shortoutput = argd['--pidonly'] or argd['--short']
        returnval = print_pids(
            knownpids,
            pidonly=shortoutput,
            used_args=argd['--args'],
            forceargs=argd['--ARGS'])

        # Print notes
        donote = (
            knownpids and
            (not shortoutput) and
            (not argd['--args']) and
            (not argd['--ARGS'])
        )
        if donote:
            print(
                ''.join((
                    '\nA * means the result was found in command arguments. ',
                    'Use -a, or -A to view them.',
                ))
            )

    return returnval


def confirm(msg):
    """ Get a user's input for confirmation.
        Returns True for yes, False for no.
    """
    if not msg:
        msg = 'Continue?'
    if not msg.endswith('?'):
        msg = ''.join((msg, '?'))
    msg = ''.join(('\n', msg, ' (y/N): '))
    answer = input(msg).lower().strip()
    return answer.startswith('y')


def get_processes(skipthisscript=True):
    """ Returns all processes running from /proc,
        Returns Dict of {"pid": {"name": "blah", "args": "blah -a"}}

        If keyword 'skipthisscript' is True, the python process currently
        running this script is omitted. [Default: True]
    """

    # build list of running process ids using /proc
    thispid = str(os.getpid())
    if skipthisscript:
        # don't inlcude this process (the python proc running this script)
        pids = [pid for pid in os.listdir('/proc')
                if (pid.isdigit() and pid != thispid)]
    else:
        # all proc pids (string), including this one.
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

    # grab info from processes
    processes = {}
    for pid in pids:
        cmdargspath = os.path.join('/proc', pid, 'cmdline')
        cmdnamepath = os.path.join('/proc', pid, 'comm')
        # dict to hold info about this process
        processinfo = {}

        # Try getting command info from /proc, skip it on failure.
        # Name
        processinfo['name'] = try_fileread(cmdnamepath)
        if processinfo['name'] is None:
            print('Read error for /proc/comm, pid: {}'.format(pid))

        # Args
        processinfo['args'] = try_fileread(cmdargspath)
        if processinfo['args'] is None:
            print('Read error for /proc/cmdline: pid: {}'.format(pid))
        elif skipthisscript and (SCRIPT in processinfo['args']):
            # Skip this script's parent process (not caught by pid earlier).
            continue

        # Save info for this pid, if it didn't fail completely.
        if processinfo['name'] or processinfo['args']:
            processes[pid] = processinfo

    return processes


def get_searchpid(pnamepat, exclude=None, firstonly=False, noargsearch=False):
    """ Returns a list with matching pids from process name.
        Pre-compiled regex pattern expected.
        Returns None on failure, a tuple of Result() on success.

        Keyword Arguments:
            exclude     : pattern to exclude matches.
            firstonly   : Only use first pid found.
            noargsearch : don't search args at all if True.
                          (boolean) - default: False
    """

    try:
        excludepat = re.compile(exclude) if exclude else None
    except re.error:
        print_fail('Invalid exclude pattern!', retcode=1)

    procs = get_processes()
    # Function to make a Result using only a pid and used_args.
    make_result = (
        lambda pid, used_args: Result(
            pid=int(pid),
            name=procs[pid]['name'],
            args=procs[pid]['args'],
            used_args=used_args)
    )

    results = []

    # If the user passed an integer (possibly pid), check to see if the
    # pid exists, and use it's info if available.
    try:
        int(pnamepat.pattern)
        # was an integer, save the pattern for procs key use.
        pidnum = pnamepat.pattern
    except (ValueError, TypeError):
        pidnum = None
    else:
        if pidnum in procs.keys():
            # User passed a valid pid number.
            results.append(make_result(pidnum, False))
            if firstonly:
                return tuple(results)

    for pid in sorted(procs, key=lambda k: int(k)):
        # grab info from this pid. (defaults to empty string if read failed.)
        pname = procs[pid]['name'] or ''
        pargs = procs[pid]['args'] or ''
        if not (pname or pargs):
            continue

        # exclude process if name matches excluded (when excluded is used)
        if excludepat and excludepat.search(pname):
            continue

        # try matching command name first.
        namematch = pnamepat.search(pname)
        usedargs = False

        if (namematch is None) and (not noargsearch):
            # try matching args (unless --noargsearch is enabled)
            namematch = pnamepat.search(pargs)
            usedargs = namematch is not None

        if namematch is not None:
            results.append(make_result(pid, usedargs))
            if firstonly:
                break

    return tuple(results)


def kill_pids(results, force=False, sigkill=False, quiet=False):
    """ Kill a list of processes by pid.
        Arguments:
            pids     : A list of pids.
            force    : No confirmation required.
            sigkill  : Use SIGKILL (-9) instead of SIGTERM.
            quiet    : When using 'force', don't print anything.
    """
    # Printing policy (if 'quiet' is used, don't print unnecessary stuff.)
    prnt = print_dummy if quiet else print

    if not results:
        return 1

    if not force:
        pidlen = len(results)
        plural = 'process' if pidlen == 1 else 'processes'
        processnames = (r.format(pidname=True) for r in results)
        msg = '\n'.join((
            'This will kill {} {}:'.format(pidlen, plural),
            '    {}'.format('\n    '.join(processnames)),
            'Do you want to continue?'
        ))
        if not confirm(msg):
            # User cancelled, display a helpful msg.
            if not quiet:
                print_cancelled()
            return 1

    sig = signal.SIGKILL if sigkill else signal.SIGTERM
    errors = 0
    # Try killing the processes.
    for result in results:
        pidfmt = '{}: {}'.format(result.pid, result.name)
        try:
            os.kill(result.pid, sig)
        except OSError as ex:
            errno = getattr(ex, 'errno', None)
            if errno == 3:
                prnt('No process with pid: {}'.format(result.pid))
            else:
                prnt('Can\'t kill {}: {}'.format(pidfmt, ex))
            errors += 1
        else:
            prnt('Killed {}'.format(pidfmt))

    return errors


def print_allprocs(exclude=None):
    """ prints all processes and info gathered with get_processes() """

    try:
        excludepat = re.compile(exclude) if exclude else None
    except re.error as ex:
        print_fail('Invalid exclude pattern: {}\n{}'.format(exclude, ex))

    procs = get_processes()
    # sort pids by integer value
    procids = sorted([int(p) for p in procs.keys()])
    proclen = len(procids)
    listed = 0
    runningmsg = 'Running processes: ({})'.format(proclen)
    print(runningmsg)
    argpad = ' ' * 10
    # cycle thru integer pids (a list comp would've added another loop)
    for pidint in procids:
        pid = str(pidint)
        # defaults to empty string if read failed during get_processes()
        pidname = procs[pid]['name'] or ''
        pidargs = procs[pid]['args'] or ''
        if excludepat and excludepat.search(pidname):
            continue
        listed += 1
        # print process info
        print('\n{:>7} : {}'.format(pid, pidname))
        if pidargs:
            print('{}{}'.format(argpad, pidargs))

    if listed < proclen:
        runningmsg = ' '.join((runningmsg, ' ...{} shown.'.format(listed)))
    print('\n{}'.format(runningmsg))
    return 0


def print_cancelled():
    """ Print the 'user cancelled' msg.
        (kept here for consistency and possible future development.)
    """
    print('\nUser cancelled.\n')


def print_dummy(*args, **kwargs):
    """ A dummy function that is compatible with print(), but does nothing.
        (for replacing print() in kill_pids())
    """
    return None


def print_fail(reason, retcode=1):
    """ prints a message and exits with return code """

    print(reason)
    sys.exit(retcode)


def print_notfound(query=None, exclude=None):
    """ Print the 'no pids found' message. """
    if query:
        print('No processes found with: {}'.format(query))
        if exclude:
            print('              Excluding: {}'.format(exclude))

    else:
        print('No processes found.')
        if exclude:
            print('Excluding: {}'.format(exclude))


def print_pids(results, pidonly=False, used_args=False, forceargs=False):
    """ prints results from pid getters. """

    if not results:
        return 1

    if pidonly:
        # Short format.
        print(','.join((r.format(pid=True) for r in results)))
        return 0

    print('pids found: ({})'.format(len(results)))
    sortedresults = sorted(results, key=lambda r: r.pid)
    # Get the longest pid's length for formatting.
    maxpidlen = len(str(sortedresults[-1].pid))
    # Print'em.
    for result in sortedresults:
        if forceargs:
            print(result.format(indent=maxpidlen))
        elif used_args:
            print(result.format(indent=maxpidlen, used_args=True))
        else:
            print(result.format(indent=maxpidlen, pidname=True))

    return 0


def try_fileread(filename):
    """ Returns data from a file, returns None on failure """

    try:
        with open(filename, 'r') as fread:
            return fread.read().replace('\n', '')
    except EnvironmentError:
        return None
    except Exception as ex:
        # General programming error.
        print_fail('Error in try_readfile(): {}'.format(ex))


class Result(object):

    """ A single search result with a pid, name, args (if any), and
        and a flag to show whether the result was found based on searching
        the arguments (used_args).
        Also includes helper methods for printing the result.
    """

    def __init__(self, pid=None, name=None, args=None, used_args=False):
        self.pid = pid
        self.name = name
        self.args = args
        self.used_args = used_args

    def __repr__(self):
        usedargs = ' * ' if self.used_args else '   '
        return '{}:{}{} {}'.format(self.pid, usedargs, self.name, self.args)

    def __str__(self):
        return self.__repr__()

    def format(self, indent=None, pid=False, pidname=False, used_args=False):
        """ A formatted string representation with options.
            Arguments:
                indent     : Integer representing the str.rjust() value.
                pid        : Use the pid only.
                pidname    : Use the pid and name only.
                used_args  : Use args only when they triggered the match.
        """
        if self.used_args:
            fmtfull = '{}: * {} {}'.format
            fmtpidname = '{}: * {}'.format

        else:
            fmtfull = '{}:   {} {}'.format
            fmtpidname = '{}:   {}'.format

        if indent is None:
            indent = 0

        if pid:
            return str(self.pid).rjust(indent)
        elif pidname:
            return fmtpidname(str(self.pid).rjust(indent), self.name)
        elif used_args:
            if self.used_args:
                return fmtfull(
                    str(self.pid).rjust(indent),
                    self.name,
                    self.args)
            return fmtpidname(str(self.pid).rjust(indent), self.name)

        # No options, just fully formatted.
        return fmtfull(str(self.pid).rjust(indent), self.name, self.args)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_tuple(cls, tup):
        return cls(*tup)

# START OF SCRIPT
if __name__ == '__main__':
    args = sys.argv[1:]
    argd = docopt(usage_str, argv=args, version=VERSIONSTR)
    ret = main(argd)
    sys.exit(ret)
