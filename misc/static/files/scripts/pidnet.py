#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" pidnet.py
    Shows network/open-file info for a pid.
    -Christopher Welborn 04-04-2016
"""

import inspect
import os
import re
import subprocess
import sys
from collections import UserList
from contextlib import suppress

from colr import (
    auto_disable as colr_auto_disable,
    Colr as C,
)
from docopt import docopt

colr_auto_disable()

NAME = 'pidnet.py'
VERSION = '0.2.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-F | -N] [-f | -q] [-D] [PROCESS...]

    Options:
        PROCESS       : Process name/pattern, or pid to use.
                        Stdin words are used when not given.
        -D,--debug    : Show some debug info while running.
        -F,--file     : Show file information.
        -f,--first    : Use first pid with usable info if multiple pids are
                        found.
        -h,--help     : Show this help message.
        -N,--net      : Show network information (default).
        -q,--quick    : Use first pid if multiple pids are found.
        -v,--version  : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

DEBUG = False


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd. """
    global DEBUG
    DEBUG = argd['--debug']

    if not (argd['--net'] or argd['--file']):
        argd['--net'] = True

    # Holds ProcResult()'s with no lsof output.
    emptypids = set()
    userargs = argd['PROCESS'] or read_stdin().strip().split()
    if not userargs:
        raise InvalidArg('No process names/patterns to use!')

    pidargs = parse_pid_args(userargs, firstonly=argd['--quick'])
    for userarg, pids in pidargs.items():
        if not pids:
            print_err('No pid found for: {}'.format(userarg))
            continue
        if argd['--quick']:
            pids = ProcResultList((pids[0], ))
        debug('Getting lsof info for arg: {} -> {}...'.format(
            userarg,
            pids.fmt(pid=True, sep=', ')[:40]
        ))
        for pidresult in pids:
            debug('  Getting lsof info for: {}'.format(
                pidresult.fmt(pid=True)
            ))
            try:
                lsof_output = get_procinfo(
                    pidresult.pid,
                    net_info=argd['--net'],
                    file_info=argd['--file']
                )
            except subprocess.CalledProcessError as exproc:
                debug('  Error: lsof returned {} for `{}`!'.format(
                    exproc.returncode,
                    ' '.join(exproc.cmd)
                ))
                lsof_output = None

            if lsof_output is None:
                continue
            elif not lsof_output:
                debug(
                    '  No info found for: {}'.format(
                        pidresult.fmt(pidname=True)
                    )
                )
                emptypids.add(pidresult)
                continue
            print(lsof_output)
            if argd['--first']:
                break

    if emptypids:
        emptylen = len(emptypids)
        pidplural = 'pid' if emptylen == 1 else 'pids'
        print('\n{} {} had no info.'.format(emptylen, pidplural))
        debug('    {}'.format(', '.join(str(p.pid) for p in emptypids)))

    return 1 if emptypids else 0


# FUNCTIONS -----------------------------------------------------------------
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
        # dict to hold info about this process
        processinfo = {}

        # Try getting command info from /proc, skip it on failure.
        # Name
        cmdnamepath = os.path.join('/proc', pid, 'comm')
        processinfo['name'] = try_fileread(cmdnamepath)
        if processinfo['name'] is None:
            print_err('Read error for /proc/comm, pid: {}'.format(pid))

        # Args
        cmdargspath = os.path.join('/proc', pid, 'cmdline')
        processinfo['args'] = try_fileread(cmdargspath)
        if processinfo['args'] is None:
            print_err('Read error for /proc/cmdline: pid: {}'.format(pid))
        elif skipthisscript and (SCRIPT in processinfo['args']):
            # Skip this script's parent process (not caught by pid earlier).
            continue
        else:
            # Separate the null-delimited args.
            processinfo['args'] = ' '.join(
                processinfo['args'].split('\x00')).strip()

        # Save info for this pid, if it didn't fail completely.
        if processinfo['name'] or processinfo['args']:
            processes[pid] = processinfo

    return processes


def get_procinfo(pid, net_info=True, file_info=False):
    """ Get process info from lsof, return the output string. """
    if not (net_info or file_info):
        raise InvalidArg('Either --net or --file must be used!')

    # build lsof command
    lsof_cmd = ['lsof']
    # apply lsof filters (if any)
    if file_info:
        # applies file names
        lsof_cmd.append('-f')
    if net_info:
        # default IPv4 filter
        lsof_cmd.extend(('-i', '4'))

    # apply AND, pid flag, and pid.
    lsof_cmd.extend(('-a', '-p', str(pid)))

    # get output of lsof
    return subprocess.check_output(lsof_cmd).decode()


def get_searchpid(
        pname, exclude=None, firstonly=False, noargsearch=False,
        procs=None):
    """ Returns a ProcResultList() with matching pids from process name.
        Pre-compiled regex pattern expected.
        Raises InvalidArg() on failure, a tuple of ProcResult() on success.

        Arguments:
            pname       : Process name/pattern/id to use.
            exclude     : Pattern to exclude matches.
            firstonly   : Only use first pid found.
            noargsearch : Don't search args at all if True.
                          (boolean) - default: False
    """
    try:
        pnamepat = re.compile(pname)
    except re.error as exre:
        raise InvalidArg('Invalid pattern: {}\n{}'.format(pname, exre))

    try:
        excludepat = re.compile(exclude) if exclude else None
    except re.error as exre:
        raise InvalidArg('Invalid exclude pattern: {}\n{}'.format(
            exclude,
            exre
        ))

    procs = procs or get_processes()

    results = ProcResultList()

    # If the user passed an integer (possibly pid), check to see if the
    # pid exists, and use it's info if available.
    try:
        int(pnamepat.pattern)
        # was an integer, save the pattern for procs key use.
        pidnum = pnamepat.pattern
    except (ValueError, TypeError):
        pidnum = None
    else:
        if pidnum in procs:
            # User passed a valid pid number.
            results.append(
                ProcResult.from_procinfo(procs, pidnum, used_args=False)
            )
            if firstonly:
                return results

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
            results.append(
                ProcResult.from_procinfo(procs, pid, used_args=usedargs)
            )
            if firstonly:
                break

    return results


def parse_pid_args(args, exclude=None, firstonly=False):
    """ Parse process names/patterns/ids into a dict of:
            { user_arg: ProcResultList(ProcResult(), ..) }
        Possibly raises InvalidArg().
    """
    procs = get_processes()
    return {
        a: get_searchpid(
            a,
            exclude=exclude,
            firstonly=firstonly,
            noargsearch=True,
            procs=procs)
        for a in args
    }


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def read_stdin():
    """ Read from stdin, print a helpful message if possible. """
    if sys.stdout.isatty() and sys.stdin.isatty():
        print('\nReading from stdin until end of file (Ctrl + D)...\n')
    return sys.stdin.read()


def try_fileread(filename):
    """ Returns data from a file, returns None on failure """

    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except EnvironmentError:
        print_err('Unable to read file: {}'.format(filename))
        return None
    except Exception as ex:
        # General programming error.
        print_err('Error in try_readfile(): {}'.format(ex))
        raise


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {}'.format(self.msg)
        return 'Invalid argument!'


class ProcResult(object):

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

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    def __repr__(self):
        usedargs = ' * ' if self.used_args else '   '
        return '{}:{}{} {}'.format(self.pid, usedargs, self.name, self.args)

    def __str__(self):
        return self.__repr__()

    def fmt(self, indent=None, pid=False, pidname=False, used_args=False):
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
    def from_procinfo(cls, procs, pid, used_args=False):
        """ Function to make a ProcResult using only a pid and used_args,
            with info from get_processes().
        """
        return cls(
            pid=int(pid),
            name=procs[pid]['name'],
            args=procs[pid]['args'],
            used_args=used_args
        )

    @classmethod
    def from_tuple(cls, tup):
        return cls(*tup)


class ProcResultList(UserList):
    def __bool__(self):
        return bool(self.data)

    def __str__(self):
        return ', '.join(str(r) for r in self.data)

    def fmt(
            self, indent=None, pid=False, pidname=False, used_args=False,
            sep='\n'):
        return (sep or '\n').join(
            r.fmt(
                indent=indent,
                pid=pid,
                pidname=pidname,
                used_args=used_args
            )
            for r in self.data
        )


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
