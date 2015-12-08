#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" pastetool.py
    ...
    -Christopher Welborn 04-19-2014
"""

from docopt import docopt
import os
import sys

# A little hack to use django_init.
scriptsdir = os.path.abspath(os.path.join(sys.path[0], '../../../scripts'))
sys.path.insert(1, scriptsdir)

NAME = 'pastetool.py'
VERSION = '1.1.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[-1]

USAGESTR = """{versionstr}
    This tool is for very specific operations, such as deleting/disabling
    expired pastes.

    For modifying a single paste, you can run the updatepaste tool
    found in /wp_site/scripts.

    Usage:
        {script} [-h | -v]
        {script} -a | -d | -D | -e | -E

    Options:
        -a,--all             : Show all pastes.
        -d,--disableexpired  : Disable expired pastes.
        -D,--deleteexpired   : Delete expired pastes. Will not delete onholds.
        -e,--expired         : Show expired pastes.
        -E,--enableexpired   : Enable expired pastes.
                               This is dangerous. It will enable all disabled,
                               expired pastes.
        -h,--help            : Show this help message.
        -v,--version         : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

# Import local stuff.
try:
    import django_init
except ImportError as eximp:
    print('\nUnable to import local stuff!\n'
          'This won\'t work!\n{}'.format(eximp))
    sys.exit(1)
# Initialize Django..
try:
    if not django_init.init_django():
        print('\nUnable to initialize django environment!')
        sys.exit(1)
except Exception as ex:
    print('\nUnable to initialize django environment!\n{}'.format(ex))
    sys.exit(1)

# Import django stuff
from apps.paste.models import wp_paste


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    if argd['--all']:
        # Show all pastes.
        return print_all()
    elif argd['--enableexpired']:
        # Enable expired pastes.
        return do_modify_expired(disabled=False)
    elif argd['--expired']:
        # Show expired pastes.
        return print_expired()
    elif argd['--deleteexpired']:
        # Delete expired pastes.
        return do_modify_expired(delete=True)
    elif argd['--disableexpired']:
        # Disable expired pastes.
        return do_modify_expired(disabled=True)
    else:
        # Default action, show expired pastes.
        return print_expired()
    return 0


def do_modify_expired(**kwargs):
    """ Modify expired pastes.
        Keyword arguments are used to set attributes on the paste.
        do_modify_expired(disabled=True)
        will set paste.disabled=True on every expired paste.

        There is one special keyword argument:
            do_modify_expired(delete=True)
            ..this will paste.delete() the expired pastes.
    """

    if not kwargs:
        print('Expecting attributes to set, or delete=True!')
        return 1

    delete = kwargs.get('delete', False)
    # The delete arg needs to be removed, so its not seen as a paste attribute
    if 'delete' in kwargs:
        kwargs.pop('delete')

    modcnt = 0
    for paste in iter_expired():
        # Deleting the pastes?
        if delete:
            if paste.onhold:
                print('    on hold: {}'.format(paste.paste_id))
            else:
                paste.delete()
                print('    deleted: {}'.format(paste.paste_id))
        else:
            # Setting attributes.
            attrset = []
            for attr in kwargs:
                attrval = kwargs[attr]
                setattr(paste, attr, attrval)
                attrset.append('{} = {}'.format(attr, attrval))
            # Save modifications
            paste.save()
            print('    set attributes for: {}'.format(paste.paste_id))
            print('        {}'.format('\n        '.join(attrset)))
        modcnt += 1

    pastestr = 'paste' if modcnt == 1 else 'pastes'
    print('\nModified {} {}.'.format(modcnt, pastestr))
    return 0


def iter_expired():
    """ Yields expired pastes. """
    try:
        pastes = wp_paste.objects.order_by('publish_date')
    except Exception as ex:
        print('\nUnable to retrieve pastes!\n{}'.format(ex))
        return

    for paste in pastes:
        if paste.is_expired(never_onhold=False):
            yield paste
        else:
            # This paste is not expired, and all other pastes are newer.
            return


def print_all():
    """ Print all pastes. Interrupt with Ctrl + C. """
    try:
        pastes = wp_paste.objects.order_by('publish_date')
    except Exception as ex:
        print('\nUnable to retrieve pastes!\n{}'.format(ex))
        return 1

    pastecnt = len(pastes)
    for paste in pastes:
        print('{!r}'.format(paste))

    plural = 'paste' if pastecnt == 1 else 'pastes'
    print('\nFound {} {}.'.format(pastecnt, plural))
    return 0 if pastecnt > 0 else 1


def print_expired():
    """ Show expired pastes. """
    try:
        pastes = wp_paste.objects.order_by('publish_date')
    except Exception as ex:
        print('\nUnable to retrieve pastes!\n{}'.format(ex))
        return 1

    expiredcnt = 0
    pastecnt = len(pastes)
    for paste in pastes:
        if paste.is_expired(never_onhold=False):
            print('expired: {!r}'.format(paste))
            expiredcnt += 1
        else:
            unexpiredcnt = pastecnt - expiredcnt
            pastestr = 'paste is' if unexpiredcnt == 1 else 'pastes are'
            print('\nThe remaining {} {} not expired.'.format(
                unexpiredcnt,
                pastestr))
            break
    expastestr = 'paste' if expiredcnt == 1 else 'pastes'
    print('\nFound {} expired {} out of {}.'.format(
        expiredcnt,
        expastestr,
        pastecnt))
    return 0


if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
