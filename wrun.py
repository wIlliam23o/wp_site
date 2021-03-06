#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""wrun.py

    Runs scripts found in ./scripts directory,
    saves from typing some, and ensures that scripts are executed properly.
"""

import os
import re
import sys
import subprocess

# Use correct input() function depending on the python version.
if sys.version < '3':
    input = raw_input  # noqa

# Usage String for help
USAGE = """wrun.py
    Usage:
        wrun.py -l
        wrun.py scriptname [scriptargs]

    Options:
        scriptname  : Name of script to run, or part of the name.
                      * Matches first script starting with 'scriptname'
        scriptargs  : One, or many, arguments to pass to the script.

        -h,--help   : Show this message.
        -l,--list   : Lists all scripts found in script directory.
"""

# Debug Mode
DEBUG = False

# Where all scripts can be found.
SCRIPTSDIR = os.path.join(os.getcwd(), 'scripts')
# Script dirs relative to the main scripts dir, and including the main dir.
SCRIPTDIRS = (
    '',  # Equates to the main scripts dir.
    '../apps/paste/scripts',
)
# Helper function for translating script dirs.
get_scriptdir = lambda s: os.path.abspath(os.path.join(SCRIPTSDIR, s))

if os.path.isdir(SCRIPTSDIR):
    sys.path.insert(1, SCRIPTSDIR)
else:
    print('\nUnable to locate scripts dir!: {}'.format(SCRIPTSDIR))
    sys.exit(1)

# Executable cmd with args and acceptable file extensions
EXECS = {
    '.py': ('python3',),
    '.sh': ('bash',),
    '.pl': ('perl',),
    '.js': ('node',),  # experimental
}


def main(args):
    """ main entry point, parses args to run scripts.
        expects args = sys.argv[1:], or
        ['scriptfiletorun.py', 'scriptarg1', 'arg2', ..]
    """

    # Get additional args for the script
    if len(args) > 1:
        scriptargs = args[1:]
    else:
        scriptargs = None

    scriptpath = find_script(args[0])

    if not scriptpath:
        print('\nCannot find that script!: {}'.format(args[0]))
        return 1

    # Check for extra input needed.
    forgotargs = check_input(scriptpath, scriptargs)
    if forgotargs:
        if not scriptargs:
            scriptargs = forgotargs
        else:
            scriptargs.extend(forgotargs)
    # Shell script..
    shellret = shell_script(scriptpath, scriptargs)
    if shellret:
        print('wrun: script returned non-zero!: {}'.format(shellret))

    return shellret


def check_input(cmdpath, cmdargs):
    if cmdargs:
        if ('-h' in cmdargs) or ('--help' in cmdargs):
            return []
        elif ('-v' in cmdargs) or ('--version' in cmdargs):
            return []

    cmdname = os.path.split(cmdpath)[-1]
    if cmdname.startswith('wprefresh'):
        print('wprefresh may require more input, checking...')
        return checkargs_wprefresh(cmdargs)
    elif cmdname.startswith('clearcache'):
        print('clearcache may require more input, checking...')
        return checkargs_clearcache(cmdargs)
    # No extra args needed
    return []


def checkargs_clearcache(cmdargs):
    """ Checks arguments for clearcache (because it may require input) """

    if cmdargs and (('-f' in cmdargs) or ('--force' in cmdargs)):
        return []

    if confirm('This will clear everthing in Django\'s cache.\n'
               'Would you like to clear the cache?'):
        # Send force arg to clearcache so it won't require any input.
        return ['--force']
    else:
        print('\nUser Cancelled\n')
        sys.exit(1)


def checkargs_wprefresh(cmdargs):
    """ Checks arguments for wprefresh (because it requires input) """
    flags = []
    # Collect Static for wprefresh
    yesforced = False
    noforced = False
    restartonly = False
    if cmdargs:
        for yesarg in ('-c', '--collect'):
            if yesarg in cmdargs:
                yesforced = True
                break
        for noarg in ('-C', '--nocollect'):
            if noarg in cmdargs:
                noforced = True
                break
        if yesforced and noforced:
            print('\nBoth \'--collect\' and \'--nocollect\' '
                  'args used, this won\'t work.')
            sys.exit(1)
        for restartarg in ('-r', '--restart'):
            if restartarg in cmdargs:
                restartonly = True
                break

    if (not yesforced) and (not noforced) and (not restartonly):
        collectstatic = input('Would you like to collect static files? '
                              '(yes/no): ')
        if collectstatic.lower().startswith('y'):
            flags.append('--collect')
        else:
            flags.append('--nocollect')
    # Get live/skip args
    liveforced = False
    skipforced = False
    if cmdargs:
        # live args used?
        for livearg in ('-l', '--live'):
            if livearg in cmdargs:
                liveforced = True
                break
        # skip args used?
        for skiparg in ('-R', '--norestart'):
            if skiparg in cmdargs:
                skipforced = True
                break

    # Ambiguos args.
    if skipforced and restartonly:
        print('\nBoth \'--restart\' and \'--norestart\' args used. '
              'this won\'t work.')
        sys.exit(1)

    if skipforced and liveforced:
        print('\nBoth \'--live\' and \'--norestart\' args used, '
              'this won\'t work.')
        sys.exit(1)

    needlive = (not liveforced) and (not skipforced)
    if (not is_test_site()) and (needlive):
        livesite = confirm('*** This is the LIVE site! ***\n'
                           'Would you like to restart apache?')
        if livesite:
            flags.append('--live')
        else:
            flags.append('--norestart')
    return flags


def confirm(s=None, default=False):
    """ Confirms an answer to a yes/no question.
        Returns True for Yes, False for No.
        Default can be given for when no answer is given.
    """

    if s:
        s = '{} (y/n): '.format(s)
    else:
        s = 'Continue? (y/n): '
    answer = input(s).strip().lower()
    return answer.startswith('y') if answer else default


def do_list():
    """ List all script files found. """

    print_debug('Getting scripts to list...')
    scripts = get_scripts()
    print('\nFound {} scripts:'.format(len(scripts)))
    curdir = None
    for scriptpath in scripts:
        thisdir, thisscript = os.path.split(scriptpath)
        if thisdir != curdir:
            # Directory change, print it.
            print('\n    {}:'.format(thisdir))
            curdir = thisdir
        # Print the filename with indention.
        print('        {}'.format(thisscript))


def get_scripts():
    execexts = EXECS.keys()
    scripts = []
    for relativedir in SCRIPTDIRS:
        scriptdir = get_scriptdir(relativedir)
        print_debug('Checking dir: {}'.format(scriptdir))
        try:
            for fname in os.listdir(scriptdir):
                print_debug('Checking file: {}'.format(fname))
                # Skip __init__.py files.
                if fname.startswith('__init__'):
                    continue
                # Add files with acceptable extensions.
                fext = os.path.splitext(fname)[-1]
                if fext in execexts:
                    scripts.append(os.path.join(scriptdir, fname))

        except (IOError, OSError) as exio:
            print_fail('Cannot list scripts dir: {}'.format(SCRIPTSDIR),
                       exc=exio)

    return sorted(scripts)


def find_script(partname, scriptlist=None):
    """ Finds a script file based on part of a name (regex),
        Returns 'scriptname' on success, or None on failure/no match.
    """

    # Helper for scripts that start with 'wp'
    if (partname.startswith('wp') or partname.startswith('^')):
        wpname = None
    else:
        wpname = 'wp{}'.format(partname)
    # Helper for scripts that start with 'update'
    if (partname.startswith('update') or partname.startswith('^')):
        updatename = None
    else:
        updatename = 'update{}'.format(partname)

    # only match switches beginning with partname to avoid ambiguous names.
    if not partname.startswith('^'):
        partname = '^{}'.format(partname)
    # compile search pattern into regex
    try:
        # Try compiling a 'wp' pattern if needed
        if wpname:
            repatwp = re.compile('^{}'.format(wpname))
        else:
            repatwp = None

        # Try compiling an 'update' pattern if needed.
        if updatename:
            repatupdate = re.compile('^{}'.format(updatename))
        else:
            repatupdate = None
        # Compile the original pattern.
        repat = re.compile(partname)
    except Exception as expat:
        print_fail('Invalid name given!: {}'.format(partname), exc=expat)

    # Load scripts if needed
    if scriptlist is None:
        scriptlist = get_scripts()
    if not scriptlist:
        print_fail('\nUnable to find any scripts!')

    # Search scripts
    for scriptpath in scriptlist:
        script = os.path.split(scriptpath)[-1]
        # Match with or without wp
        rematch = repat.search(script)
        if rematch:
            return scriptpath
        else:
            if repatwp:
                # try wpname
                rematch = repatwp.search(script)
                if rematch:
                    return scriptpath
            if repatupdate:
                # try updatescript
                rematch = repatupdate.search(script)
                if rematch:
                    return scriptpath

    # No match
    return None


def is_test_site():
    cwd = os.getcwd()
    return ('test' in cwd) or ('cj/workspace' in cwd)


def shell_script(scriptfile, args=None):
    """ Shell a script, including script args.
        Determines which interpreter to use based on file extension.
    """
    # retrieve executable for this script.
    try:
        cmdargs = EXECS[scriptfile[-3:]]
    except Exception as ex:
        print_fail('Cannot locate executable for this script: '
                   '{}'.format(scriptfile),
                   exc=ex)
    # build command list for subprocess
    cmdlst = list(cmdargs)
    cmdlst.append(scriptfile)
    if args:
        cmdlst.extend(args)

    # run/create process
    print('\nRunning: {}\n'.format(' '.join(cmdlst)))
    # Shell the process, returns the subprocess.Popen() proc object.
    proc = run_process(cmdlst)
    # Print stdout/stderr
    retcode = print_proc_output(proc)

    return retcode


def run_process(cmdlist):
    """ Wraps subprocess.Popen to print output from a process,
        cmdlist = command list that Popen() expects.
    """

    try:
        proc = subprocess.Popen(cmdlist,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except Exception as exproc:
        cmdstr = ' '.join(cmdlist[:3])
        print_fail('Error opening process!: {} ...'.format(cmdstr), exc=exproc)
        return None
    return proc


def parse_commands(args):
    """ Parse the arg list, run any commands before looking up a script name
    """

    # command flags, mapped to their function.
    commands = {
        '-l': {
            'aliases': ['--list'],
            'func': do_list,
            'kwargs': None,
        },
        '-h': {
            'aliases': ['--help'],
            'func': print_usage,
            'kwargs': {'retcode': 0},
        },
    }

    # Setup list of known flags...
    commandflags = list(commands.keys())
    aliasesgen = (commands[cmdflag]['aliases'] for cmdflag in commands.keys())
    for cmdaliases in aliasesgen:
        commandflags += cmdaliases
    commandflags.sort()

    # Function to retrive a flag by its name, or alias.
    def get_flag(flagname):
        """ Retrieve a flag function by name, or alias. """
        if flagname in commands.keys():
            return commands[flagname]
        else:
            for cmdflag in commands.keys():
                if flagname in commands[cmdflag]['aliases']:
                    return commands[cmdflag]

    # wrun commands must come before any script file.
    commandargs = []
    while ((args) and (args[0].startswith('-'))):
        commandargs.append(args.pop(0))

    # Retrieve functions for flags, and call them..
    for cmdarg in commandargs:
        if cmdarg in commandflags:
            # known flag, retrieve the function for it and call it.
            command = get_flag(cmdarg)
            commandkw = command['kwargs']
            commandfunc = command['func']
            if commandkw:
                print_debug('Running command option function with args...')
                commandfunc(**commandkw)
            else:
                print_debug('Running command option function...')
                commandfunc()
        else:
            # unknown flag!
            print_fail((
                'Unknown flag given!: {}\n'
                'Run with --help for usage instructions.'
            ).format(cmdarg))

    # Return args without any 'wrun command flags'.
    return args


def print_debug(obj):
    """ Prints a message,
        or if list of strings is passed it formats the output better
    """

    if not DEBUG:
        return False

    if hasattr(obj, 'lower'):
        # string/unicode... just print it.
        print('Debug: {}'.format(obj))
    elif isinstance(obj, (list, tuple)):
        # list/tuple, format it...
        header = 'Debug: '
        spaces = (' ' * len(header))
        if obj:
            print('{}{}'.format(header, obj[0]))
        if len(obj) > 1:
            otherlines = '\n{}'.format(spaces).join(obj[1:])
            print('\n{}{}'.format(spaces, otherlines))
    else:
        # different type of object
        print('Debug: {!r}'.format(obj))

    return True


def print_fail(msg, exc=None, retcode=1):
    """ prints a message and exits
        Keyword Args:
            exc     = an optional  Exception to print before exiting
            retcode = Return code to return, default: 1
    """

    print('\n{}'.format(msg))
    if exc:
        print('\n{}'.format(str(exc)))
    sys.exit(retcode)


def print_proc_output(proc):
    """ Prints output from a subprocess.Popen() proc.
    """
    if not proc:
        print('print_proc_output({}): No process!'.format(proc))
        return 1

    # Print any stdout.
    for line in iter(proc.stdout.readline, ''):
        if line:
            print(line.decode('utf-8').strip('\n'))
        else:
            break
    # Print any stderr.
    for eline in iter(proc.stderr.readline, ''):
        if eline:
            print(eline.decode('utf-8').strip('\n'))
        else:
            break

    if proc.returncode is not None:
        return proc.returncode
    return 0


def print_usage(retcode=None):
    """ Print the usage string. """

    print(USAGE)

    if retcode is not None:
        sys.exit(retcode)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage(retcode=1)
    # Run any commands before looking up a script name.
    parsedargs = parse_commands(sys.argv[1:])
    if not parsedargs:
        sys.exit(0)

    ret = main(parsedargs)
    sys.exit(ret)
