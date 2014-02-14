#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" clearcache.py
    Clears django's cache for the Welborn Productions site.
    wprefresh.py can do this while refreshing the site,
    but sometimes all you need is a cache-clear.
    
    -Christopher Welborn 02-13-2014
"""

import os
import sys

from docopt import docopt

NAME = 'WpClearCache'
VERSION = '1.0.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[-1]

USAGESTR = """{versionstr}
    Usage:
        {script} [-f | -h | -v]

    Options:
        -f,--force    : Force cache clear, no confirmation.
        -h,--help     : Show this help message.
        -v,--version  : Show version.
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

# Import Django stuff.
from django.core.cache import cache


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    
    if not argd['--force']:
        print('\nThis will remove everything from Django\'s cache.')
        if not confirm('Are you sure you want to clear it?'):
            print('\nUser Cancelled.\n')
            return 1
    try:
        cache.clear()
    except Exception as ex:
        print('\nError clearing the cache:\n{}'.format(ex))
        return 1
    print('\nCache was cleared.')
    return 0


def confirm(s=None):
    """ Confirm a yes/no answer. Returns True/False for Yes/No. """

    if s:
        s = '{} (y/n): '.format(s)
    else:
        s = 'Continue? (y/n): '

    answer = input(s).strip().lower()
    return answer.startswith('y')

if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
