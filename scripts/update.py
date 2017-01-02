#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" update.py
    Update/view info for models in this project.
    -Christopher Welborn 01-01-2017
"""

import os
import sys

import warnings

from django.utils.deprecation import RemovedInDjango19Warning

warnings.filterwarnings(action='ignore', category=RemovedInDjango19Warning)


def import_err(name, exc, module=None, local=False):
    """ Print a helpful message for missing third-party/local libraries. """
    if local:
        msg = 'Missing local library file: {}\n  {}'.format(name, exc)
    else:
        msg = '\n'.join((
            'You are missing a library: {name}',
            'You can install it with pip: `pip install {module}`',
            'The original message was: {exc}'
        )).format(name=name, module=module or name.lower(), exc=exc)
    print(msg, file=sys.stderr)
    sys.exit(1)


try:
    from colr import (
        Colr as C,
        auto_disable as colr_auto_disable,
    )
except ImportError as ex:
    import_err('Colr', ex)
colr_auto_disable()

try:
    from colr import docopt
except ImportError as ex:
    import_err('Docopt', ex)
try:
    from printdebug import DebugColrPrinter
except ImportError as ex:
    import_err('PrintDebug', ex)

try:
    import django_init
    if not django_init.init_django():
        print('\nUnable to initialize django!', file=sys.stderr)
        sys.exit(1)
except ImportError as ex:
    import_err('django_init.py', ex, local=True)

try:
    import objectupdater
except ImportError as ex:
    import_err('objectupdater.py', ex, local=True)

try:
    from wp_main.utilities import utilities
except ImportError as ex:
    import_err('{e.name}'.format(e=ex), ex, local=True)

debugprinter = DebugColrPrinter()
debugprinter.disable()
debug = debugprinter.debug

NAME = 'WpUpdate'
VERSION = '0.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -L | -v                  [-D]
        {script} APP [-f | -l]                 [-D]
        {script} APP -A FILE...                [-D]
        {script} APP ID... -a [-F]             [-D]
        {script} APP IDENT [-d | -l | -j | -p] [-D]
        {script} APP IDENT -u data             [-D]

    Options:
        FILE                   : One or more archive files to create objects
                                 from.
        ID                     : Same as IDENT, except multiple ids can be
                                 used.
        IDENT                  : Identifier to lookup and object.
                                 These are set in the app's update.py.
        APP                    : App to work with.
                                 Use -L to list available apps.
        -a,--archive           : Show archive string for an object.
                                 When -F is used, data is written to file.
        -A,--ARCHIVE           : Load object from archive file.
        -d,--delete            : Delete an object (confirmation needed).
        -D,--debug             : Show some debug info while running.
        -f,--fields            : List model fields.
        -F,--file              : When archiving, write to file.
        -h,--help              : Show this message.
        -j,--json              : Show JSON string for an object.
        -l,--list              : List detailed object info, or summary if
                                 no args were given.
        -L,--listapps          : List updateable apps.
        -p,--pickle            : Show Pickle string for an object.
        -u data,--update data  : Update object info with attribute:value
                                 or "attribute:spaced value"
        -v,--version           : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

# Apps must have an update.py that implements these attributes/functions:
# This maps from attr/function: sanity-check-function
must_implement = {
    # Proper name for the app, with title case.
    'name': lambda a: isinstance(a, str),
    # The actual model class to work with. Must have an 'objects' attr.
    'model': lambda s: hasattr(s, 'objects'),
    # Attributes to search when looking up by name, an iterable (title, name,)
    'attrs': lambda t: objectupdater.is_iterable(t),
    # A function that prints the objects to stdout.
    'do_list': callable,
}

# Set after init, see the bottom.
UPDATEABLE_APPS = tuple()


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd. """
    if argd['--listapps']:
        return do_list_apps()

    # Any other action requires an app name to work with.
    appmodule = get_app_by_name(argd['APP'])
    # TODO: Pass a single object with all the info needed, grabbed from
    #       the app itself (maybe in an updater.py module)
    ident = argd['ID'] if argd['--archive'] else argd['IDENT']

    # Function map for simple object operations.
    id_funcs = {
        '--archive': {
            'func': objectupdater.do_objects_archive,
            'kwargs': {'usefile': argd['--file']},
        },
        '--delete': {
            'func': objectupdater.do_object_delete,
        },
        '--list': {
            'func': objectupdater.do_object_info,
        },
        '--json': {
            'func': objectupdater.do_object_json,
        },
        '--pickle': {
            'func': objectupdater.do_object_pickle,
        },
        '--update': {
            'func': objectupdater.do_object_update,
            'kwargs': {'data': argd['--update']},
        },
    }

    if argd['--ARCHIVE']:
        # Create objects from archives.
        return objectupdater.do_objects_fromarchives(argd['FILE'])
    elif argd['--list'] and (not argd['IDENT']):
        return appmodule.do_list()
    elif argd['--fields']:
        return objectupdater.do_fields(appmodule.model)
    elif argd['IDENT']:
        # ID specific functions..
        for id_flag in id_funcs.keys():
            if not argd[id_flag]:
                continue
            do_func = id_funcs[id_flag]['func']
            if 'kwargs' in id_funcs[id_flag].keys():
                do_kwargs = id_funcs[id_flag]['kwargs']
                return do_func(ident, appmodule, **do_kwargs)
            return do_func(ident, appmodule)

        # Unhandled args, or no args.
        # No args with identifier (do Header String print)
        return objectupdater.do_headerstr(ident, appmodule)

    # Default behavior (no args)
    return 0 if appmodule.do_list() else 1


def do_list_apps():
    """ List all apps found with a valid update.py. """
    if not UPDATEABLE_APPS:
        raise ValueError('No updateable apps found!')

    for appmodule in UPDATEABLE_APPS:
        print('{:>16}: {}'.format(appmodule.name, appmodule.__file__))

    print('\nUpdateable apps: {}'.format(len(UPDATEABLE_APPS)))
    return 0


def get_app_by_name(name):
    """ Search app.update modules by name. If the update.py has an `aliases`
        attribute, allow `name` to match those aliases.
    """
    name = name.strip().lower()
    debug('Searching for app: {}'.format(name))
    for updatemod in UPDATEABLE_APPS:
        if updatemod.name.strip().lower() == name:
            debug('Found app by name: {}'.format(name))
            return updatemod
        aliases = getattr(updatemod, 'aliases', [])
        for alias in aliases:
            if alias.strip().lower() == name:
                debug('Found app by alias: {}'.format(name))
                return updatemod
    raise InvalidArg('No app found by name: {}'.format(name))


def get_updateable():
    """ Returns only apps that are updateable by updater. """
    return utilities.get_apps(
        include=is_updateable,
        child='update'
    )


def is_updateable(updatemod):
    """ Checks whether a update.py implements all the must-have functions.
        Returns True on success, prints a message and returns False on error.
    """

    # Updater can be disabled simply by putting 'disabled = True' in the
    # module.
    disabled = getattr(updatemod, 'disabled', False)
    if disabled:
        return False

    missing = []
    wrongtypes = []
    _nothing = object()
    for attr, attrchecker in must_implement.items():
        attrval = getattr(updatemod, attr, _nothing)
        if attrval is _nothing:
            missing.append(attr)
            continue
        elif not attrchecker(attrval):
            wrongtypes.append((attr, type(attrval).__name__))
            continue
        elif attrval is None:
            wrongtypes.append((attr, type(attrval).__name__))
            continue

    name = getattr(updatemod, '__name__', '{!r}'.format(updatemod))
    if missing:
        print_err('\n'.join((
            'Module {name} is missing update attributes:',
            '    {attrs}'
        )).format(name=name, attrs='\n    '.join(missing)))
        return False
    elif wrongtypes:
        print_err(
            '\n'.join((
                'Module {name} has some wrong attribute types:',
                '    {attrs}'
            )).format(
                name=name,
                attrs='\n    '.join(
                    '{name} (type: {type})'.format(name=n, type=t)
                    for n, t in wrongtypes
                )
            )
        )
    debug('Found updateable app: {}'.format(updatemod.name))
    # Module implements all the needed attributes/functions.
    return True


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(
        C(kwargs.get('sep', ' ').join(str(a) for a in args), 'red'),
        **kwargs
    )


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {}'.format(self.msg)
        return 'Invalid argument!'


UPDATEABLE_APPS = get_updateable()

if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR, script=SCRIPT))
    except (ValueError, InvalidArg) as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\nBroken pipe, input/output was interrupted.\n')
        mainret = 3
    sys.exit(mainret)
