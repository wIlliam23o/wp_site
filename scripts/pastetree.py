#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" pastetree.py
    Testing the display of pastes in a 'tree' format.
    root ->
        child1 ->
            child1
            child2
        child2 ->
            child1
    
    -Christopher Welborn 03-27-2014
"""

from docopt import docopt
from collections import namedtuple
import os
import sys

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

NAME = 'pastetree.py'
VERSION = '1.0.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[-1]

USAGESTR = """{versionstr}
    Usage:
        {script} [-h | -v]

    Options:
        -h,--help     : Show this help message.
        -v,--version  : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

IterResult = namedtuple('IterResult', ['level', 'paste'])


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """

    x = 0
    for iterresult in iter_pastes():
        printresult(iterresult)
        x += 1

    print('Printed {} pastes...'.format(x))
    return 0


def iter_children(paste, level=1):
    """ Iterate over all children of a paste, and children's children. """
    for p in paste.children.filter(disabled=False).order_by('publish_date'):
        yield IterResult(level, p)
        if p.children.count() > 0:
            yield from iter_children(p, level=level + 1)


def iter_pastes(startpastes=None):
    """ Iterate over all pastes that have no parent.
        Given a 'startpastes' list, it will start from that paste only.
    """
    if startpastes is None:
        pastes = wp_paste.objects.filter(disabled=False, parent=None)
        pastes = pastes.order_by('publish_date')
    else:
        pastes = [startpastes]

    for p in pastes:
        yield IterResult(0, p)
        if p.children.count() > 0:
            yield from iter_children(p, level=0)


def pastestr(p):
    """ Format a paste for printing (different from str(paste)) """
    return '{} {} ({})'.format(p.publish_date, p.title, p.view_count)


def printresult(iresult):
    """ Print a tuple result from iter_children/iter_pastes """
    indention = '  ' * iresult.level

    print('{}: {}{}'.format(iresult.level, indention, pastestr(iresult.paste)))


if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
