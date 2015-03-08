#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Statistics
     @summary: Gathers info about blog/project views/downloads and any other
               info I can grab.

      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 25, 2013
'''

import inspect
import os
import sys

from docopt import docopt
NAME = 'WpStats'
VERSION = '2.0.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[-1]

USAGESTR = """{version}
    Usage:
        {script} [-h | -v] [-D]
        {script} ([-a] [-b] [-d] [-i] [-m] [-p] [-P]) [-D]

    Options:
        -a,--app        : Show apps info.
        -b,--blog       : Show blog info.
        -d,--download   : Show downloads info.
        -D,--debug      : Show debugging info.
        -h,--help       : Show this help message.
        -i,--img        : Show image info.
        -m,--misc       : Show misc info.
        -p,--project    : Show project info.
        -P,--paste      : Show paste info.
        -v,--version    : Show {name} version and exit.
""".format(name=NAME, version=VERSIONSTR, script=SCRIPT)

# Setup django environment
try:
    try:
        # Import style for django.
        from scripts import django_init
    except ImportError:
        # Import style for cmdline.
        import django_init
    if not django_init.init_django():
        sys.exit(1)
except ImportError as eximp:
    print('\nUnable to import django_init.py!:\n{}'.format(eximp))
    sys.exit(1)
except Exception as ex:
    print('\nUnable to initialize django environment!:\n{}'.format(ex))
    sys.exit(1)

# Import welbornprod stuff
try:
    # Model info.
    from apps.models import wp_app
    from apps.paste.models import wp_paste
    from blogger.models import wp_blog
    from projects.models import wp_project
    from downloads.models import file_tracker
    from img.models import wp_image
    from misc.models import wp_misc

    # Stats tools.
    from stats.tools import get_model_info, get_models_info

except ImportError as eximp:
    print("unable to import welbornprod modules!\n" +
          "are you in the right directory?\n\n" + str(eximp))
    sys.exit(1)

modelopts = {
    file_tracker: {
        'orderby': '-download_count',
        'displayattr': 'shortname'
    },
    wp_app: {
        'orderby': '-view_count',
        'displayattr': 'name'
    },
    wp_blog: {
        'orderby': '-view_count',
        'displayattr': 'slug'
    },
    wp_image: {
        'orderby': '-view_count',
        'displayattr': ('image_id', 'title', 'image.name'),
        'displayformat': '{image_id} - {title} ({image-name})'
    },
    wp_misc: {
        'orderby': '-download_count',
        'displayattr': 'name'
    },
    wp_paste: {
        'orderby': '-view_count',
        'displayattr': ('paste_id', 'title'),
        'displayformat': '{paste_id} - {title}'
    },
    wp_project: {
        'orderby': '-download_count',
        'displayattr': 'name'
    }
}

argmap = {
    '--app': wp_app,
    '--blog': wp_blog,
    '--download': file_tracker,
    '--img': wp_image,
    '--misc': wp_misc,
    '--project': wp_project,
    '--paste': wp_paste
}

DEBUG = False


def main(argd):
    """ Main entry point for wpstats. """
    global DEBUG
    DEBUG = argd['--debug']

    filtered = False
    # Check for user args, only show stats for user given args.
    for arg in sorted(argmap):
        model = argmap[arg]
        if argd[arg]:
            filtered = True
            model = argmap[arg]
            modelinfo = get_model_info(model, **modelopts[model])
            if modelinfo:
                print('\n{}'.format(modelinfo))

    if not filtered:
        print_all()
    return 0


def debug(s=None, short_filename=True, fmt=None):
    """ Print debugging info only if DEBUG is false. """
    if not DEBUG:
        return None
    # Not this frame (print_lineinfo()), but the one before it (the caller).
    frame = inspect.currentframe().f_back
    # Use the filename only when short_filename is specified.
    fname = frame.f_code.co_filename
    try:
        lineinfo = (fmt if fmt else '{file}: #{line} {func}()').format(
            file=os.path.split(fname)[-1] if short_filename else fname,
            line=frame.f_lineno,
            func=frame.f_code.co_name)
    except (IndexError, KeyError, ValueError) as ex:
        # Most likely the format string was wrong, give a more helpful msg.
        helpex = ex.__class__('\n  '.join((
            'Format string must have all names: {file} {line} {func}',
            'Got: {}'.format(fmt)
        )))
        raise helpex from ex
    print(': '.join((lineinfo, s)) if s else lineinfo)


def print_all():
    """ Prints stats for all models/objects. """
    modelinfo = get_models_info(modelopts)
    for statgrp in modelinfo:
        print('\n{}'.format(statgrp))


# START OF SCRIPT
if __name__ == "__main__":
    sys.exit(main(docopt(USAGESTR, version=VERSIONSTR)))
