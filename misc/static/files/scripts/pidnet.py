#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" pidnet.py
    Shows network connections being used by applications.
"""

import sys
import commands

def main(args):
    # parse args
    argdict = get_args(args)
    # help?
    if get_arg(argdict, '-h'):
        print_help(exit_code=0)
    elif get_arg(argdict, '-a'):
        # debug....
        print_args(argdict)
        sys.exit(0)
    
    # get process to work with.
    pid = get_arg(argdict, 'pid')
    pname = get_arg(argdict, 'name')
    # no valid pname/pid?
    if (not pid) and (not pname):
        print 'no process id or name given!'
        sys.exit(1)
    
    # get pid from name
    if pname:
        pid = get_pidfromname(pname, usefirst = get_arg(argdict, '-s'))
        if pid == '':
            print 'no process found for: ' + pname
            sys.exit(1)
        elif ' ' in pid:
            # several processes named
            print 'more than one process named: ' + pname
            print pid
            print 'run the program again with the current pid instead of a name,'
            print 'or run pidnet with the -s flag to choose the first pid found.'
            sys.exit(1)
    
    # build lsof command
    lsof_cmd = ['lsof']
    # apply lsof filters (if any)
    if get_arg(argdict, '-f'):
        # applies file names
        lsof_cmd.append('-f')
    else:
        # default IPv4 filter
        lsof_cmd += ['-i', '4']
    
    # apply AND, pid flag, and pid.
    lsof_cmd += ['-a', '-p', pid]
    
    # get output of lsof
    lsof_cmd_str = ' '.join(lsof_cmd)
    if get_arg(argdict, '-d'): print 'running command: ' + lsof_cmd_str
    results = commands.getoutput(lsof_cmd_str)
    if results == '':
        if get_arg(argdict, '-f'):
            sresult = 'sorry, no open net or file info for: ' + pid
        else:
            sresult = 'sorry, no open net info for: ' + pid + '\n' + \
                      'the -f flag will list open files if any are found.'
        print sresult
        sys.exit(1)
    
    results_lines = results.split('\n')
    if get_arg(argdict, '-f'):
        # show open files too
        filter_ = None
    else:
        # only show network info
        filter_ = 'IPv4'
    
    # print results
    fixed_results = format_results(results_lines, filter_txt = filter_)
    for sline in fixed_results:
        print sline
    # finished
    sys.exit(0)
    
# FUNCTIONS -------------------------------------------------------------------
def get_pidfromname(pname, usefirst=False):
    """ returns the pid by process name using pidof.
        fails on multiple pids (prints results, and exits).
    """
    # start command list
    pid_cmd = ['pidof']
    # use first available pid?
    if usefirst:
        pid_cmd.append('-s')
        
    # add process name to command
    pid_cmd.append(pname)
    # run command
    pid = commands.getoutput(' '.join(pid_cmd))
    return pid


def format_results(results_list, filter_txt = None):
    """ format results list, filtering if needed. returns formatted list """
    
    header = results_list[0]
    results = sorted(results_list[1:])
    
    formatted = [header]
    for line_ in results:
        if filter_txt is None:
            formatted.append(line_)
        else:
            if filter_txt in line_:
                formatted.append(line_)
    return formatted

def get_args(args):
    """ formats/locates args no matter the position. """

    pid = None
    pname = None
    argdict = {}
    for arg in args:
        if arg.startswith('-'):
            # flag argument.
            farg = arg
            if farg.startswith('--'):
                while farg.startswith('--'):
                    farg = farg.replace('--', '-')
                # get short arg version.
                farg = farg[0:2]
                if farg == '-':
                    print 'invalid argument passed: ' + arg
                else:
                    argdict[farg] = True
            else:
                if len(farg) > 2:
                    # multiple args in one flag.
                    for char in farg:
                        if char == '-':
                            pass
                        elif char == '':
                            print 'invalid argument passed: ' + argdict
                        else:
                            argdict['-' + char] = True
                else:
                    argdict[farg] = True
                        
        else:
            # process id or name
            try:
                pid = int(arg)
            except:
                pname = arg
    
    if pid is not None:
        argdict['pid'] = str(pid)
    if pname is not None:
        argdict['name'] = pname
    
    # do some sorting, just because (debug print)
    sorted_keys = sorted(argdict)
    sorteddict = {}
    for skey in sorted_keys:
        sorteddict[skey] = argdict[skey]
        
    # return results
    return sorteddict

def get_arg(argdict, argname):
    """ safely retrieve argument """
    if argdict.has_key(argname):
        return argdict[argname]
    else:
        return False
        

def print_args(argdict):
    for argkey in argdict.keys():
        print argkey + ': ' + str(argdict[argkey])


def print_usage(exit_code=None):
    print 'usage: pidnet.py <process id | process name> [options]\n'
    if exit_code is not None: sys.exit(exit_code)

    
def print_help(exit_code=None):
    print_usage()
    print 'pidnet help:\n' + \
          '    options:\n' + \
          '        -h : show this message\n' + \
          '        -f : show open files too\n' + \
          '        -s : use first pid if multiple ids are found for name\n'
          
    if exit_code is not None: sys.exit(exit_code)

# MAIN SCRIPT START -----------------------------------------------------------    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage(exit_code=1)
    else:
        main(sys.argv[1:])
