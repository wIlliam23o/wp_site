#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" pidname
    
    gets the pid of a known process name,
    or searches all processes for part of name, returns possible pids.

    Christopher Welborn
"""

import os
import re
import sys

from docopt import docopt

_NAME = 'PidName'
__VERSION__ = '1.2.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, __VERSION__)
_FILE = os.path.split(sys.argv[0])[1] if '/' in sys.argv[0] else sys.argv[0]
_SCRIPT = _FILE[:-3] if _FILE.endswith('.py') else _FILE

usage_str = """{versionstr}

    Usage:
        {script} -h
        {script} -l
        {script} <name> [options]
        {script} <name> -e <excludename> [options]

    Options:
        <name>                              : known process name, or name to 
                                              search for (regex allowed).
                                              you can also enter a known pid
                                              for reverse lookup.
        -h,--help                           : show this message.
        -a,--args                           : include command arguments in
                                              results when found.
        -A,--ARGS                           : always include command arguments
                                              in results.
        -e <excluded>,--exclude <excluded>  : exclude any process names
                                              matching this regex.
                                              by default one process is always
                                              excluded, the 'pidname' process.
                                              it would list false-positives
                                              when searching process args.
        -l,--list                           : list all running processes with
                                              arguments.
        -n,--noargsearch                    : don't search arguments for match.
        -p,--pidonly                        : searches only names (no args),
                                              prints only the first pid found.
        -s,--short                          : use short output suitable for
                                              chaining with another program.
                                              multiple pids are separated by
                                              a comma.
        -v,--version                        : show {script} version.
        

""".format(versionstr=_VERSIONSTR, script=_SCRIPT)


def main(argd):
    """ Main entry point, receives args from docopt. """
    
    # catch process --list command.
    if argd['--list']:
        print_allprocs()
        return 0
    
    # Get name query from docopt args.
    pname = argd['<name>']
    
    # try compiling as a regex
    try:
        pnamepat = re.compile(pname)
    except Exception as expat:
        print_fail('Invalid name/search-term given!: '
                   '{}\n{}'.format(pname, expat))
    
    # run search, certain cmdline options are passed to the search function.
    knownpids = get_searchpid(pnamepat,
                              includeargs=argd['--args'],
                              forceargs=argd['--ARGS'],
                              forceshort=argd['--short'],
                              excluded=argd['--exclude'],
                              noargsearch=argd['--noargsearch'],
                              pidonly=argd['--pidonly'],
                              )
    
    # Finished retrieving/searching.
    shortoutput = argd['--pidonly'] or argd['--short']
    returnval = print_pids(knownpids, pidonly=shortoutput)
    
    # Print notes
    if ((not shortoutput) and
       (not argd['--args']) and
       (not argd['--ARGS']) and knownpids):
        print(''.join([
            '\nA * means the result was found in command arguments. ',
            'Use -a, or -A to view them.',
        ]))
    
    return returnval


def get_searchpid(pnamepat, **kwargs):
    """ Returns a list with matching pids from process name.
        Pre-compiled regex pattern expected.
        Returns None on failure.
        
        Keyword Arguments:
            includeargs : include arguments in results when used.
                          (boolean) - default: False
            forceargs   : always include arguments in results.
                          (boolean) - default: False
            forceshort  : always use short output (pid only)
                          (boolean) - default: False
            noargsearch : don't search args at all if True.
                          (boolean) - default: False
            pidonly     : only output pid, nothing else.
                          (boolean) - default: False

    """
    
    # parse keyword args
    includeargs = kwargs.get('includeargs', False)
    forceargs = kwargs.get('forceargs', False)
    forceshort = kwargs.get('forceshort', False)
    noargsearch = kwargs.get('noargsearch', False)
    pidonly = kwargs.get('pidonly', False)
    excluded = kwargs.get('excluded', None)

    try:
        excludepat = re.compile(excluded) if excluded else None
    except:
        print_fail('Invalid exclude pattern!', retcode=1)

    def format_name(pname, pargs, usedargs=False):
        """ Format a found pid's name (with or without args) """
        if forceargs:
            # args always included
            pname = pargs
        elif (usedargs and includeargs):
            # args only included when used
            pname = pargs
        elif (usedargs):
            # args not included, but used and marked.
            pname = pname + " *"
        return pname

    procs = get_processes()
    results = []
    
    # If the user passed an integer (possibly pid), check to see if the
    # pid exists, and print it's info if available.
    try:
        pidnum = int(pnamepat.pattern)
        # was an integer, save the pattern for procs key use.
        pidnum = pnamepat.pattern
    except (ValueError, TypeError):
        pidnum = None
    if pidnum and (pidnum in procs.keys()):

        # User passed a valid pid number.
        pname = '' if procs[pidnum]['name'] is None else procs[pidnum]['name']
        pargs = '' if procs[pidnum]['args'] is None else procs[pidnum]['args']
        pname = format_name(pname, pargs, usedargs=False)
        results.append('{} : {}'.format(pidnum, pname))

    for pid in procs.keys():
        # grab info from this pid. (defaults to empty string if read failed.)
        pname = '' if procs[pid]['name'] is None else procs[pid]['name']
        pargs = '' if procs[pid]['args'] is None else procs[pid]['args']
                           
        # exclude process if name matches excluded (when excluded is used)
        if excluded:
            excludematch = excludepat.search(pname)
            if excludematch:
                continue
        
        # try matching command name first.
        namematch = pnamepat.search(pname)
        usedargs = False
        
        if namematch is None:
            # try matching args (unless --noargsearch is enabled)
            namematch = None if noargsearch else pnamepat.search(pargs)
            if namematch:
                usedargs = True
            
        if namematch is not None:
            # Found a pid, format the name according to user options.
            pname = format_name(pname, pargs, usedargs=usedargs)
 
            # add this match
            if pidonly:
                # only list pids (args don't count for --pidonly,
                #                 it includes pidname itself because of args.)
                if not usedargs:
                    results.append(pid)

            else:
                # use pid and process name (args too if included above.)
                if forceshort:
                    results.append(pid)
                else:
                    results.append('{} : {}'.format(pid, pname))
    
    return results


def try_fileread(filename):
    """ Returns data from a file, returns None on failure """
        
    try:
        with open(filename, 'r') as fread:
            return fread.read().replace('\n', '')
    except (IOError, OSError):
        return None
    

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
            print('...skipping ' + pid + '/comm, (read error)')
        
        # Args
        processinfo['args'] = try_fileread(cmdargspath)
        if processinfo['args'] is None:
            print('...skipping ' + pid + '/cmdline, (read error)')
            
        # Save info for this pid, if it didn't fail completely.
        if processinfo['name'] or processinfo['args']:
            processes[pid] = processinfo
        
    return processes


def print_allprocs():
    """ prints all processes and info gathered with get_processes() """

    procs = get_processes()
    # sort pids by integer value
    procids = sorted([int(p) for p in procs.keys()])
    proclen = str(len(procids))
    print('Running processes: (' + proclen + ')')
    # cycle thru integer pids (a list comprehension would've added another loop)
    for pidint in procids:
        pid = str(pidint)
        # defaults to empty string if read failed during get_processes()
        pidname = '' if procs[pid]['name'] is None else procs[pid]['name']
        pidargs = '' if procs[pid]['args'] is None else procs[pid]['args']
        
        # print process info
        print('\n    ' + pid + ' : ' + pidname)
        if len(pidargs) > 0:
            print((' ' * (len(pid) + 7)) + pidargs)
    
    print('\nRunning processes: (' + proclen + ')')
    return 0


def print_pids(pids, pidonly=False):
    """ prints results from pid getters. """
    
    if (pids is None) or (len(pids) == 0):
        if not pidonly:
            print('No pid found!')
        return 1
    
    if not pidonly:
        print('pids found: (' + str(len(pids)) + ')')
    
    if pidonly:
        print(','.join(pids))
    else:
        for pid in sorted(pids):
            print('    ' + pid)

    return 0


def print_fail(reason, retcode=1):
    """ prints a message and exits with return code """
    
    print(reason)
    sys.exit(retcode)


# START OF SCRIPT
if __name__ == '__main__':
    args = sys.argv[1:]
    argd = docopt(usage_str, argv=args, version=_VERSIONSTR)
    ret = main(argd)
    sys.exit(ret)
