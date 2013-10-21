#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" pidname
    
    gets the pid of a known process name,
    or searches all processes for part of name, returns possible pids.

    Christopher Welborn
"""

usage_str = """pidname

    Usage:
        pidname.py -h
        pidname.py -l
        pidname.py <name> [options]
        pidname.py <name> -e <excludename> [options]

    Options:
        <name>                              : known process name, or name to search for (regex allowed).
        -h,--help                           : show this message.
        -a,--args                           : include command arguments in results when found.
        -A,--ARGS                           : always include command arguments in results.
        -e <excluded>,--exclude <excluded>  : exclude any process names matching this regex.
        -l,--list                           : list all running processes with arguments.
        -p,--pidonly                        : same as --short.
        -s,--short                          : use short output suitable for chaining with another program.
                                              (first if many are found).
        

"""

from docopt import docopt
import sys, os, commands, re
import os.path

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
        print_fail('Invalid name/search-term given!: ' + str(pname))
    
    # use short format? (pids only)
    pidonly = (argd['--pidonly'] or argd['--short'])
    # run search, certain cmdline options are passed to the search function.
    knownpids = get_searchpid(pnamepat, 
                              includeargs=argd['--args'],
                              forceargs=argd['--ARGS'],
                              excluded=argd['--exclude'],
                              pidonly=pidonly
                             )
    
    # Finished retrieving/searching.
    returnval = print_pids(knownpids, pidonly=pidonly)
    
    # Print notes
    if (not pidonly) and (not argd['--args']) and (not argd['--ARGS']) and knownpids:
        print('\nA * means the result was found in command arguments. Use -a, or -A to view them.')
    
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
            pidonly     : only output pid, nothing else.
                          (boolean) - default: False
    """
    
    # parse keyword args
    includeargs = kwargs.get('includeargs', False)
    forceargs = kwargs.get('forceargs', False)
    pidonly = kwargs.get('pidonly', False)
    excluded = kwargs.get('excluded', None)
    try:
        excludepat = re.compile(excluded) if excluded else None
    except:
        print_fail('Invalid exclude pattern!', retcode=1)
    
    procs = get_processes()
    results = []
    
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
            # try matching args.
            namematch = pnamepat.search(pargs)
            usedargs = True
            
        if namematch is not None:
            # found a match, return "pid : command name (possibly with args)"
            if forceargs:
                # args always included
                pname = pargs
            elif (usedargs and includeargs):
                # args only included when used
                pname = pargs
            elif (usedargs):
                # args not included, but used and marked.
                pname = pname + " *"
 
            # add this match
            if pidonly and (not usedargs):
                # only list pids (args don't count for --pidonly, it includes pidname itself because of args.)
                results.append(pid)
            else:
                # use pid and process name (args too if included above.)
                results.append(pid + " : " + pname)
    
    return results

def try_fileread(filename):
    """ Returns data from a file, returns None on failure """
        
    try:
        with open(filename, 'r') as fread:
            return fread.read().replace('\n', '')
    except (IOError, OSError) as exread:
        return None
    

def get_processes(skipthisscript = True):
    """ Returns all processes running from /proc,
        Returns Dict of {"pid": {"name": "blah", "args": "blah -a"}}

        If keyword 'skipthisscript' is True, the python process currently 
        running this script is omitted. [Default: True]
    """
    
    
    # build list of running process ids using /proc
    thispid = str(os.getpid())
    if skipthisscript:
        # don't inlcude this process (the python proc running this script)
        pids = [pid for pid in os.listdir('/proc') if (pid.isdigit() and pid != thispid)]
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


def print_fail(reason, retcode = 1):
    """ prints a message and exits with return code """
    
    print(reason)
    sys.exit(retcode)


# START OF SCRIPT
if __name__ == '__main__':
    args = sys.argv[1:]
    argd = docopt(usage_str, argv=args)
    ret = main(argd)
    sys.exit(ret)

