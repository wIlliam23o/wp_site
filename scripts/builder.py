#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" builder.py
    Builds the Welborn Productions site.
    Right now it just makes sure to minify all javascript.
"""

import os
import sys
import subprocess
import time

from docopt import docopt

# Import local stuff.
try:
    import django_init
except ImportError as eximp:
    print('\nUnable to import local stuff!\nThis won\'t work!\n{}'.format(eximp))
    sys.exit(1)

_FILE = sys.argv[0]
_SCRIPT = os.path.split(_FILE)[1]
_NAME = 'Builder'
_VERSION = '1.0.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, _VERSION)
DEBUG = False

# Minimum time in minutes for a file to be considered newly modified.
# if (now - file.modifiedtime) < MIN_TIME (minutes): process the file.
# if there is no .min file, it will be processed anyways.
MIN_TIME = 10

# Initialize Django..
try:
    if not django_init.init_django(sys.path[0]):
        print('\nUnable to initialize django environment!')
        sys.exit(1)
except Exception as ex:
    print('\nUnable to initialize django environment!\n{}'.format(ex))
    sys.exit(1)
# Import Django stuff.
from django.conf import settings

usage_str = """{versionstr}

    Usage:
        {script} -h | -v
        {script} <file> [-d]
        {script} [-i strings] [-f strings] [-m minutes] [-d]
        {script} -c | -j [-i strings] [-f strings] [-m minutes] [-d]

    Options:
        <file>                 : Build a single file.
        -c,--css               : Build only .css files.
        -d,--debug             : Debug, doesn't actually build anything.
        -f str,--filtered str  : Comma-separated list of strings to filter out.
        -h,--help              : Show this message.
        -i str,--included str  : Comma-separated list of strings to include.
        -j,--js                : Build only .js files.
        -m min,--modtime min   : Minimum last-modified duration to rebuild a file. (in minutes)
        -v,--version           : Show {name} version.
""".format(name=_NAME, script=_SCRIPT, versionstr=_VERSIONSTR)


def main(argd):
    """ main entry point, expects arg dict from docopt(). """
    global DEBUG, MIN_TIME
    DEBUG = argd['--debug']
    
    included = parse_commas(argd['--included'])
    filtered = parse_commas(argd['--filtered'])
    MIN_TIME = parse_modtime(argd['--modtime'])

    if argd['<file>']:
        # Build a single file.
        ret = build_file(argd['<file>'])
    else:
        if argd['--js']:
            # Build JS
            ret = build_js_files(included=included, filtered=filtered)
        elif argd['--css']:
            # Build CSS
            ret = build_css_files(included=included, filtered=filtered)
        else:
            # Build all files.
            ret = build_all(included=included, filtered=filtered)
            if not ret:
                print('\nBuild all: failures!')

    return 0 if ret else 1


def build_all(included=None, filtered=None, forced=False):
    """ Basically runs all build functions available. """
    
    allreturns = []
    jsret = build_js_files(included=included, filtered=filtered, forced=forced)
    allreturns.append(jsret)
    if not jsret:
        print('\nBuild js: Failed')
    
    cssret = build_css_files(included=included, filtered=filtered, forced=forced)
    allreturns.append(cssret)
    if not cssret:
        print('\nBuild css: Failed')

    return all(allreturns)


def build_css_file(filename):
    """ Build a single css file. """

    try:
        yui = get_external_tool('yuicompressor.jar')
    except ToolNotFound:
        raise

    outfile = filename.replace('.css', '.min.css')

    cmdargs = ['java', '-jar', yui, filename, '-o', outfile]

    procret = subprocess.check_call(cmdargs)
    return (procret == 0)


def build_css_files(included=None, filtered=None, forced=False):
    """ Builds all css files. """

    if filtered and not 'min' in filtered:
        filtered.append('min')
    else:
        filtered = ['min']

    #@TODO: This is the same as build_js_files except closure is used! Combine them!
    print('\nGathering css files...')
    cssfiles = get_files_byext('.css', included=included, filtered=filtered, forced=forced)
    for filename in cssfiles:
        try:
            status = filename
            if DEBUG:
                procret = True
            else:
                procret = build_css_file(filename)
            if procret:
                status = '{}: Success'.format(filename)
            else:
                status = '{}: Fail'.format(filename)
            print(status)
        except Exception as ex:
            print('\nUnable to build css files!:\n{}'.format(ex))
            return False

    print('\nBuild css: Success ({} files)'.format(str(len(cssfiles))))
    return True


def build_file(filenameshort):
    """ Find a files fullpath, determine builder, and build it. """
    filename = find_file(filenameshort)
    if not filename:
        print('\nUnable to locate that file: {}'.format(filenameshort))
        return 1
    print('Found file: {}'.format(filename))

    builder = get_builder_func(filename)
    if not builder:
        print('\nUnable to find a builder for that file: {}'.format(filename))
        return 1
    
    if DEBUG:
        ret = True
    else:
        ret = builder(filename)
    if ret:
        print('Successful build: {}'.format(filename))
    else:
        print('Unable to build: {}'.format(filename))
    return 0 if ret else 1


def build_js_file(filename):
    """ Minify a single js file. """
    
    try:
        closure = get_external_tool('closure.jar')
    except ToolNotFound:
        raise
    
    # Build command args: java -jar closure.jar --language_in ECMASCRIPT5 --js ${1} --js_output_file $OUTFILE
    outfile = filename.replace('.js', '.min.js')
    
    cmdargs = ['java', '-jar', closure, '--language_in', 'ECMASCRIPT5', '--js', filename, '--js_output_file', outfile]
    
    procret = subprocess.check_call(cmdargs)
    return (procret == 0)


def build_js_files(included=None, filtered=None, forced=False):
    """ builds all js files. """
    
    if filtered and not 'min' in filtered:
        filtered.append('min')
    else:
        filtered = ['min']
    
    print('\nGathering js files...')
    jsfiles = get_files_byext('.js', included=included, filtered=filtered, forced=False)
    for filename in jsfiles:
        #skipfile = is_skip_file(filename, included=included, filtered=filtered)

        # if skipfile:
        #    continue
        try:
            status = filename
            if DEBUG:
                procret = True
            else:
                procret = build_js_file(filename)
            if procret:
                status = '{}: Success'.format(filename)
            else:
                status = '{}: Fail'.format(filename)
            print(status)
        except Exception as ex:
            print('\nUnable to build js files!:\n{}'.format(ex))
            return False

    print('\nBuild js: Success ({} files)'.format(str(len(jsfiles))))
    return True


def find_file(filename):
    """ Retrieves full path for file. """
    for fullpath in get_files_byext(filename[-3:]):
        if fullpath.endswith('{}'.format(filename)):
            return fullpath
    return None


def get_builder_func(filename):
    """ Retrieve the proper builder function for a filename. """
    
    builders = {'.js': build_js_file,
                '.css': build_css_file,
                }
    
    for builderext in builders.keys():
        if filename.endswith(builderext):
            return builders[builderext]
    return None


def get_external_tool(toolfile):
    """ Gets the absolute path for an external script. """
    fullpath = os.path.join(settings.BASE_DIR, 'scripts/external', toolfile)
    if not os.path.isfile(fullpath):
        print('\nUnable to find external tool: {}'.format(fullpath))
        raise ToolNotFound('Unable to locate: {}'.format(toolfile))
    return fullpath


def get_files_byext(ext, included=None, filtered=None, forced=False):
    """ Retrieve all static files by extension.
        Arguments:
            ext       : File must end with 'ext' to count.
        Keyword Arguments:
            filtered  : List of strings that will exclude a file from matching.
                        Example: get_files_byext('.js', ['min']) # Filters out .min.js files.
            included  : List of string that will include a file. (exclude takes precedence)
            forced    : Boolean, files aren't updated if last-modified time is < MIN_TIME,
                        unless forced == True.
    """
    
    foundfiles = []
    for root, dirs, files in os.walk(settings.BASE_DIR):  # @UnusedVariable: dirs
        
        # Only look in static dirs.
        if not '/static' in root:
            continue
        
        for filename in files:
            # Only get files with matching extension.
            if filename.endswith(ext):
                fullpath = os.path.join(root, filename)
                if not is_skip_file(fullpath, included=included, filtered=filtered, forced=forced):
                    foundfiles.append(fullpath)
                    if DEBUG:
                        print('Found file: {}'.format(filename))
    return foundfiles


def get_modified_duration(filename):
    """ Get the time in minutes since last modification of this file. """

    fileextparts = os.path.splitext(filename)
    filebase = fileextparts[0]
    is_min = filebase.endswith('.min')
    fileext = fileextparts[-1]

    # Check if a min file exists. Force creation if it doesn't.
    if not is_min:
        minfile = '{}.min{}'.format(filebase, fileext)
        if not os.path.isfile(minfile):
            # No min file, has never been created. (force it)
            print('\nNew file: {}'.format(filename))
            return 0

    try:
        modtime = os.path.getmtime(filename)
    except Exception as ex:
        print('\nCan\'t stat file: {}\n{}'.format(filename, ex))
        # Force re-building.
        return 0

    secondselapsed = time.time() - modtime
    return secondselapsed / 60


def get_parent_dir(filename):
    """ Retrieves directory for a file. """
    return os.path.split(filename)[0]


def is_skip_file(filename, included=None, filtered=None, forced=False):
    """ Determines if this file should be built using included and filtered strings. """
    
    if forced:
        return False

    skipfile = False
    filenameshort = os.path.split(filename)[1] if '/' in filename else filename

    if included:
        for includestr in included:
            if not includestr in filenameshort:
                skipfile = True
                break

    if filtered:
        for filterstr in filtered:
            if filterstr in filenameshort:
                skipfile = True
                break

    # Get last modified time...
    if not skipfile:
        modtime = get_modified_duration(filename)
        if DEBUG:
            print(filenameshort + ' - Minutes since modification: ' + str(modtime))
        if modtime > MIN_TIME:
            return True

    return skipfile


def parse_commas(s):
    """ Parses a comma separated string into a list.
        Returns None on failure.
    """
    
    if not s:
        return None
    s = s.strip('"').strip("'")
    if ',' in s:
        items = [i.strip() for i in s.split()]
    else:
        items = [s.strip()]

    return items


def parse_modtime(s):
    """ Parses the --modtime arg, returns the default MIN_TIME on failure. """

    if not s:
        return MIN_TIME

    try:
        ftime = float(s)
        return ftime
    except:
        print('\nInvalid value for --modtime!: {}\n..using the default.'.format(s))
        return MIN_TIME


class ToolNotFound(Exception):
    pass


# START OF SCRIPT
if __name__ == '__main__':
    mainargd = docopt(usage_str, version=_VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)
