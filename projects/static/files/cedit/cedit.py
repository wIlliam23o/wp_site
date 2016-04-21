#!/usr/bin/env python3
'''
    cedit.py
    Opens proper editor based on file extension..
    Checks file permissions, asks for root access if needed..

Created on Jan 19, 2013

@author: cj
'''
from __future__ import print_function
import os
import stat
import sys

from docopt import docopt
from easysettings import EasySettings
if sys.version_info.major < 3:
    input = raw_input


NAME = 'CEdit'
__version__ = '2.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, __version__)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])
OPTIONS = {
    'editor': 'editor to open files.',
    'elevcmd': 'elevation command for when root is needed.'
}
settings = EasySettings(os.path.join(SCRIPTDIR, 'cedit.conf'))

USAGESTR = """{ver}

    Opens files with your favorite editor,
    and uses an elevation command automatically when needed for
    write access.

    Usage:
        {script} -h | -l | -v
        {script} -s option...
        {script} FILENAME

    Options:
        FILENAME                : File name to open or create.
        -h,--help               : shows this message
        -l,--list               : lists current settings
        -s option,--set option  : sets a {name} option
                                  current options are:
                                    editor=[path to editor]
                                    elevcmd=[path to elevation command]
                                  to set default editor:
                                    {script} -s editor=gedit
                                  to set default elevation command:
                                    {script} -s elevcmd=sudo
        -v,--version            : Show cedit version and exit.

    {name} will look for a config file in: {scriptdir}
""".format(name=NAME, script=SCRIPT, scriptdir=SCRIPTDIR, ver=VERSIONSTR)


def main(argd):
    """ Main entry point for cedit """

    settings.configfile_exists()

    if argd['--list']:
        configopts = settings.list_settings()
        if not configopts:
            print('No settings configured.')
            return 1
        print('Current cedit settings:')
        print('    {}'.format('\n    '.join(
            '{:>8}: {}'.format(k, v) for k, v in configopts)))
        return 0
    elif argd['--set']:
        return 0 if set_option(argd['--set']) else 1

    if not os.path.exists(argd['FILENAME']):
        print('Path does not exist: {}'.format(argd['FILENAME']))
        sres = input('Would you like to use it anyway? (y/n): ')
        if not sres.lower().startswith('y'):
            print('Quitting...\n')
            exit(0)

    return 0 if shell_file(argd['FILENAME']) else 1


def get_editor():
    if not settings.get('editor'):
        # no editor set
        print('\n' / join((
            'Be sure to set your favorite editor with:',
            '    cedit -s editor=[path_to_editor]'
        )))
        # look for common editor
        lst_editors = ['kate', 'gedit', 'leafpad', 'kwrite']
        for editor in lst_editors:
            spath = os.path.join('/usr/bin/', editor)
            if os.path.isfile(spath) or os.path.islink(spath):
                print('Found common editor: {}'.format(spath))
                return spath
        print('\n'.join((
            'No common editors found!',
            'You must set one using the above command.'
        )))
        exit(1)
    else:
        editor = settings.get('editor')
        if os.path.isfile(editor) or os.path.islink(editor):
            return editor
        else:
            # try /usr/bin
            spath = os.path.join('/usr/bin', editor)
            if os.path.isfile(spath) or os.path.islink(spath):
                return spath
        print('\n'.join((
            'Cannot find editor! Make sure you set a valid editor with:'
            'cedit -s editor=[editor or /path/to/editor]'
        )))
        exit(1)


def get_elevcmd():
    if not settings.get('elevcmd'):
        # no editor set
        print('\n'.join((
            'Be sure to set your favorite elevation command with:',
            '    cedit -s elevcmd=[elevation command]'
        )))
        # look for common elevation command
        lst_elevs = ['kdesudo', 'gksudo', 'sudo']
        for elevcmd in lst_elevs:
            spath = os.path.join('/usr/bin/', elevcmd)
            if os.path.isfile(spath) or os.path.islink(spath):
                print("Found common elevation cmd: " + spath)
                return spath
        print('\n'.join((
            'No common elevation commands found!',
            'You must set one using the above command.'
        )))
        sys.exit(1)
    else:
        elevcmd = settings.get('elevcmd')
        if os.path.isfile(elevcmd) or os.path.islink(elevcmd):
            return elevcmd
        else:
            # try /usr/bin
            spath = os.path.join('/usr/bin', elevcmd)
            if os.path.isfile(spath) or os.path.islink(spath):
                return spath
        print('\n'.join((
            'Cannot find elevcmd!',
            'Make sure you set a valid elevation command with:',
            '    cedit -s elevcmd=[elevcmd or /path/to/elevcmd]'
        )))
        sys.exit(1)


def set_option(args):
    for sarg in args:
        try:
            sopt, sval = (s.lower().strip() for s in sarg.split('='))
        except ValueError:
            print('Invalid config option given: {}'.format(sarg))
            return False

        if sopt not in OPTIONS:
            print('{} is not a valid option!'.format(sopt))
            print('Accepted options are:')
            for opt, desc in OPTIONS.items():
                print('    {}: {}'.format(opt, desc))
            sys.exit(1)
        if (not os.path.isfile(sval)) and (not os.path.islink(sval)):
            spath = os.path.join('/usr/bin/', sval)
            if (not os.path.isfile(spath)) and (not os.path.islink(spath)):
                print('Cannot set option \'{}\', path not found: {}'.format(
                    sopt, sval
                ))
                sys.exit(1)
            else:
                sval = spath

        if settings.get(sopt) == sval:
            print('{} already set to: {}'.format(sopt, sval))
            sys.exit(1)
        # valid setting, set it
        settings.setsave(sopt, sval)
        print('    set {} = {}'.format(sopt, sval))
    return True


def needs_root(sfilename):
    """ Return True if a file needs root write permissions. """
    try:
        if os.access(sfilename, os.W_OK):
            # User already has write access.
            return False
        # File is owned by root?
        return (os.stat(sfilename).st_uid == 0)
    except OSError:
        # TODO: Some logging is needed here.
        return True


def shell_file(sfilename):
    editor = get_editor()
    if not editor.startswith("/"):
        editor = '/usr/bin/{}'.format(editor)
    if not os.path.isfile(editor):
        print('Editor not found!: {}'.format(editor))
        return False

    print('Using editor: {}'.format(editor))
    if os.path.isfile(sfilename):
        filetype = 'file'
    elif os.path.isdir(sfilename):
        filetype = 'directory'
    else:
        filetype = 'an unknown type'
    print('Opening {}...'.format(filetype))
    if needs_root(sfilename):
        # root style.
        elevcmd = get_elevcmd()
        cmd = [elevcmd, editor, sfilename]
        print('Using elevation command...')
    else:
        # normal style, no root.
        cmd = [editor, sfilename]
    try:
        # try running
        run_exec(cmd)
        print('Ran {}'.format(' '.join(cmd)))
    except Exception as ex:
        print('Unable to run command: {}\nError: {}'.format(
            ' '.join(cmd),
            ex))
        return False
    return True


def run_exec(cmdlist):
    # runs a command with arguments.
    os.system(' '.join(cmdlist))

if __name__ == '__main__':
    sys.exit(main(docopt(USAGESTR, version=VERSIONSTR)))
