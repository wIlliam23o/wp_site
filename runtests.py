#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" runtests.py
    ...
    -Christopher Welborn 09-02-2015
"""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner
from docopt import docopt

NAME = 'Run WP Tests'
VERSION = '0.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-F] [-k] [-r] [-p pat] [-V num] [APP...]

    Options:
        APP                     : App name to test.
        -F,--failfast           : Exit on first failure.
        -h,--help               : Show this help message.
        -k,--keepdb             : Keep database between test runs.
        -p pat,--pattern pat    : File pattern to decide while files to test.
        -r,--reverse            : Reverse the order of test execution.
        -v,--version            : Show version.
        -V num,--verbosity num  : Either 1 or 2 for verbosity.
                                  Default: 2
""".format(script=SCRIPT, versionstr=VERSIONSTR)


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd. """
    TestRunner = get_runner(settings)
    test_runner = TestRunner(
        verbosity=int_arg(
            argd['--verbosity'],
            default=2,
            minval=1,
            maxval=2),
        failfast=argd['--failfast'],
        keepdb=argd['--keepdb'],
        pattern=argd['--pattern'],
        reverse=argd['--reverse'])

    failures = test_runner.run_tests(argd['APP'])
    if failures:
        print('\nFailures: {}'.format(failures))
    return failures


def int_arg(s, default=None, minval=None, maxval=None):
    """ Parse an argument as an integer. Clamp it if needed.
        If None is passed, default is returned.
    """
    if not s:
        return default
    try:
        val = int(s)
    except ValueError:
        print('\nInvalid number: {}'.format(s))
        sys.exit(1)
    if (minval is not None) and val < minval:
        return minval
    if (maxval is not None) and val < maxval:
        return maxval

    return val

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'wp_main.settings'
    django.setup()

    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
