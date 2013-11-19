#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" builder.py
    Helps to build the Welborn Productions site.
    Looks for .scss (Sass) files to build, and
    When .css or .js files are modified, a new .min file needs to be created.
    This script helps to automate that process by checking last-modified times,
    and allows you to build single files, or certain extensions,
    and filter which files should be built.

    This is meant to be incorporated into the wprefresh.py script, so doing a
    refresh will also include any new changes to .js or .css files, plus any
    other file that may need 'building' in the future.

    -Christopher Welborn 2013
"""

import os
import re
import sys
import subprocess
import time

from docopt import docopt

# Import local stuff.
try:
    import django_init
except ImportError as eximp:
    print('\nUnable to import local stuff!\n'
          'This won\'t work!\n{}'.format(eximp))
    sys.exit(1)
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

_FILE = sys.argv[0]
_SCRIPT = os.path.split(_FILE)[1]
_NAME = 'Builder'
_VERSION = '1.0.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, _VERSION)
DEBUG = False
# These strings will always be filtered.
DEFAULT_FILTERS = ['.min.', '-min.', '_welbornprod.scss']
# These are the default extensions to use (when build_files() is called)
DEFAULT_EXTENSIONS = ['.css', '.js', '.scss']

# Strings for skip reasons..
SKIP_REASON_TABLE = {'filtered': '(filtered)        ',
                     'defaultfiltered': '(default filtered)',
                     'modifiedtime': '(modified-time)   ',
                     'forced': '(forced)          ',
                     'notincluded': '(not included)    ',
                     'passed': '(passed)          ',
                     }

# Flag for when the master SASS file has changed (_welbornprod.scss)
MASTER_SASS_MODIFIED = False
MASTER_SASS_MODTIME = -1
MASTER_SASS_CHECKED = False
MASTER_SASS_FILE = os.path.join(settings.BASE_DIR,
                                'wp_main/static/sass/_welbornprod.scss')

usage_str = """{versionstr}

    Usage:
        {script} -h | -v
        {script} [-a] [-i strings] [-f strings] [-p] [-d]
        {script} <file>... [-a] [-i strings] [-f string] [-p] [-d]
        {script} -c [-a] [-i strings] [-f strings] [-p] [-d]
        {script} -j [-a] [-i strings] [-f strings] [-p] [-d]
        {script} -s [-a] [-i strings] [-f strings] [-p] [-d]

    Options:
        <file>                 : One or multiple files to build.
                                 (no filename builds all)
        -a,--all               : Build all files, ignore filters/includes and
                                 modification status.
        -c,--css               : Build only .css files.
        -d,--debug             : Debug, doesn't actually build anything.
                                 Use this to find out which files would be
                                 built, or why they wouldn't be built.
        -f str,--filtered str  : Comma-separated list of strings to filter out.
        -h,--help              : Show this message.
        -i str,--included str  : Comma-separated list of strings to include.
        -j,--js                : Build only .js files.
        -p,--path              : When filtering/including match the whole path,
                                 not just the filename.
        -s,--sass              : Build only .scss files.
        -v,--version           : Show {name} version.
""".format(name=_NAME, script=_SCRIPT, versionstr=_VERSIONSTR)


def main(argd):
    """ main entry point, expects arg dict from docopt(). """
    global DEBUG, MIN_TIME
    DEBUG = argd['--debug']

    included = parse_commas(argd['--included'])
    filtered = parse_commas(argd['--filtered'])
    buildargs = {'included': included,
                 'filtered': filtered,
                 'forced': argd['--all'],
                 'matchpath': argd['--path'],
                 }

    if argd['<file>']:
        # Build a single file.
        statusargs = {'method': 'Multiple', 'filecount': len(argd['<file>'])}
        statusargs.update(buildargs)
        print_buildstatus(**statusargs)
        ret = build_files(argd['<file>'], **buildargs)
    else:
        # No files passed,  build all, or certain extensions.

        if argd['--js']:
            # Build JS
            statusargs = {'method': 'JS'}
            statusargs.update(buildargs)
            print_buildstatus(**statusargs)
            ret = build_js_files(**buildargs)
        elif argd['--sass']:
            # Build SASS
            statusargs = {'method': 'SASS'}
            statusargs.update(buildargs)
            print_buildstatus(**statusargs)
            ret = build_sass_files(**buildargs)
        elif argd['--css']:
            # Build CSS
            statusargs = {'method': 'CSS'}
            statusargs.update(buildargs)
            print_buildstatus(**statusargs)
            ret = build_css_files(**buildargs)
        else:
            # Build all files.
            print_buildstatus(**buildargs)
            ret = build_all(**buildargs)
            if not ret:
                print('\nBuild all: failures!')

    return 0 if ret else 1


def build_all(**kwargs):
    """ Basically runs all build functions available.
        For keyword arguments see: walk_files_byext()
    """

    allreturns = []
    jsret = build_js_files(**kwargs)
    allreturns.append(jsret)
    if not jsret:
        print('\nBuild js: Failed')

    # Sass must come before css!
    sassret = build_sass_files(**kwargs)
    allreturns.append(sassret)
    if not sassret:
        print('\nBuild sass: Failed!')

    cssret = build_css_files(**kwargs)
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


def build_css_files(**kwargs):
    """ Builds all css files. see walk_files_byext() for keyword arguments """

    #@TODO: This is the same as build_js_files except closure is used!
    #@TODO: Combine them!

    print('\nBuilding CSS...')
    # Get walker (Generator) for these files/filters
    cssfiles = walk_files_byext('.css', **kwargs)
    totallen = 0
    for filename in cssfiles:
        try:
            status = filename
            if DEBUG:
                procret = True
            else:
                procret = build_css_file(filename)
            if procret:
                status = '{}: Success'.format(trim_filename(filename))
                totallen += 1
            else:
                status = '{}: Fail'.format(trim_filename(filename))
            print(status)
        except Exception as ex:
            print('\nUnable to build css files!:\n{}'.format(ex))
            return False

    print('\nBuild css: Success ({} files)'.format(str(totallen)))
    return True


def build_file(filenameshort):
    """ Find a files fullpath, determine builder, and build it. """
    if DEBUG:
        print('\nBuilding single file: {}'.format(filenameshort))

    filename = find_file(filenameshort, forced=True)
    if not filename:
        print('\nUnable to locate that file: {}'.format(filenameshort))
        return 1
    print(' Found file: {}'.format(filename))

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


def build_files(filenames, **kwargs):
    """ Build multiple files, builder function is determined by the extension.
        Arguments:
            filenames  : List of filenames to build
                         (can be shortnames, find_file() is used.)

        Keyword Arguments:
            see is_skip_file()...
    """
    if not filenames:
        print('\nNo files to build!')
        return 1

    successcount = 0
    failurecount = 0

    if DEBUG:
        print('Building files:\n    {}'.format('\n    '.join(filenames)))

    def get_file_list():
        if DEBUG:
            print('\nRetrieving list of file names...')
        getargs = {k: v for k, v in kwargs.items()}
        getargs['forced'] = True
        getargs['silent'] = True
        defaults = DEFAULT_EXTENSIONS
        shortname = lambda s: os.path.split(s)[1]
        return {shortname(f): f for f in get_files_byext(defaults, **getargs)}

    def _find_in_list(f):
        if not filelist:
            print('\nFile list is not initialized!')
            return None
        if f in filelist.keys():
            return filelist[f]
        else:
            fvals = filelist.values()
            if f in fvals:
                return fvals[fvals.index(f)]
        return None

    filelist = None
    for filenameshort in filenames:
        # Initialize file list for the first item.
        if os.path.exists(filenameshort):
            filename = filenameshort
        else:
            # Need to retrieve long name.
            if not filelist:
                # Build the initial file list..
                filelist = get_file_list()
            # Try to retrieve the file.
            filename = _find_in_list(filenameshort)

        if not filename:
            print('\nUnable to locate that file!: {}'.format(filenameshort))
            return 1

        # Skip file?
        skipfile, skipreason = is_skip_file(filename, **kwargs)
        if skipfile:
            if DEBUG:
                print('     Skip file {}: {}'.format(skipreason,
                                                     trim_filename(filename)))
            continue

        builder = get_builder_func(filename)
        if not builder:
            print('\nUnable to find a builder for that file:'
                  ' {}'.format(filename))
            return 1

        if DEBUG:
            ret = True
        else:
            ret = builder(filename)

        statusstr = '{}: '.format(trim_filename(filename))
        if ret:
            successcount += 1
            print('{}Success'.format(statusstr))
        else:
            print('{}Failed'.format(statusstr))
            failurecount += 1

    if failurecount > 0:
        print('\nBuild files: Failures ' +
              '({} successes, {} failures)'.format(str(successcount),
                                                   str(failurecount)))
    else:
        print('\nBuild files: Success ({} files)'.format(str(successcount)))

    return 1 if (failurecount > 0) else 0


def build_js_file(filename):
    """ Minify a single js file. """

    try:
        closure = get_external_tool('closure.jar')
    except ToolNotFound:
        raise

    # Build command args:
    outfile = filename.replace('.js', '.min.js')

    cmdargs = ['java', '-jar', closure, '--language_in', 'ECMASCRIPT5',
               '--js', filename, '--js_output_file', outfile]

    procret = subprocess.check_call(cmdargs)
    return (procret == 0)


def build_js_files(**kwargs):
    """ builds all js files. see walk_files_byext() for keyword arguments """

    print('\nBuilding JS...')
    # Get walker (Generator) for these files/filters
    jsfiles = walk_files_byext('.js', **kwargs)
    totallen = 0
    for filename in jsfiles:
        try:
            status = filename
            if DEBUG:
                procret = True
            else:
                procret = build_js_file(filename)
            if procret:
                status = '{}: Success'.format(trim_filename(filename))
                totallen += 1
            else:
                status = '{}: Fail'.format(trim_filename(filename))
            print(status)
        except Exception as ex:
            print('\nUnable to build js files!:\n{}'.format(ex))
            return False

    print('\nBuild js: Success ({} files)'.format(str(totallen)))
    return True


def build_sass_file(filename):
    """ Builds a single .scss file. """
    try:
        sass = get_external_tool('sass')
    except ToolNotFound:
        raise

    # Get sass includes dir.
    includesdir = os.path.join(settings.BASE_DIR, 'wp_main/static/sass')
    if not os.path.isdir(includesdir):
        print('\nUnable to locate wp_main/static/sass includes dir!\n'
              'Looked in: {}'.format(includesdir))
        return False

    outfile = get_sass_targetfile(filename)
    if not outfile:
        return False

    # Build command args:
    #     sass -I $project_path/wp_main/static/sass $INFILE $OUTFILE
    cmdargs = [sass, '-I', includesdir, filename, outfile]

    procret = subprocess.check_call(cmdargs)
    return (procret == 0)


def build_sass_files(**kwargs):
    """ builds all sass files (.scss), see walk_files_byext() for kwargs. """

    print('\nBuilding SASS...')
    # Get walker (Generator) for these files/filters
    sassfiles = walk_files_byext('.scss', **kwargs)
    totallen = 0
    for filename in sassfiles:
        try:
            status = filename
            if DEBUG:
                procret = True
            else:
                procret = build_sass_file(filename)
            if procret:
                status = '{}: Success'.format(trim_filename(filename))
                totallen += 1
            else:
                status = '{}: Fail'.format(trim_filename(filename))
            print(status)
        except Exception as ex:
            print('\nUnable to build sass files!:\n{}'.format(ex))
            return False

    print('\nBuild sass: Success ({} files)'.format(str(totallen)))
    return True


def find_file(filename, silent=True, forced=False):
    """ Retrieves full path for file. """
    for fullpath in walk_files_byext(filename[-3:],
                                     silent=silent,
                                     forced=forced):
        print('\nChecking: {}\n    With: {}'.format(fullpath, filename))

        if fullpath.endswith(filename):
            return fullpath
    return None


def get_builder_func(filename):
    """ Retrieve the proper builder function for a filename. """

    builders = {'.js': build_js_file,
                '.css': build_css_file,
                '.scss': build_sass_file,
                }

    for builderext in builders.keys():
        if filename.endswith(builderext):
            return builders[builderext]
    return None


def get_external_tool(toolfile):
    """ Gets the absolute path for an external script. """

    notfoundmsg = '\nUnable to find external tool: {}'.format(toolfile)
    notfounderr = ToolNotFound('Unable to locate: {}'.format(toolfile))

    # Look in scripts/external dir first..
    fullpath = os.path.join(settings.BASE_DIR, 'scripts/external', toolfile)
    if os.path.isfile(fullpath):
        return fullpath

    # Use `which` to determine location..
    cmdargs = ['which', toolfile]
    try:
        rawoutput = subprocess.check_output(cmdargs).decode('utf-8').strip('\n')
    except subprocess.CalledProcessError:
        # which returned non-zero, command not found.
        print(notfoundmsg)
        raise notfounderr
    except Exception as ex:
        # Error when running 'which'!
        print('\nError when running `which`!:\n{}'.format(ex))
        raise notfounderr
    # Get fixed command output.
    fullpath = rawoutput.decode('utf-8').strip('\n')

    # Check output.
    if not os.path.isfile(fullpath):
        print(notfoundmsg)
        raise notfounderr
    # Good path, return it.
    return fullpath


def get_files_byext(ext, **kwargs):
    """ Get a list of all files by extension.
        see walk_files_byext() for arguments/keyword arguments
    """

    extfiles = [f for f in walk_files_byext(ext, **kwargs)]

    return extfiles


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


def get_sass_targetfile(filename):
    """ Gets the target .css file path for a .scss file. """
    # Get parent dir for /sass and filename..
    sasspat = re.compile('([/\w\d]+)/sass/([\w\d\-\.]+)')
    rematch = sasspat.search(filename)
    if not rematch:
        print('\nNot a .scss file, or incorrect dir!: {}'.format(filename))
        return False

    # Get out file for scss. (moves to ../css/filename.css)
    try:
        parentdir, shortfile = rematch.groups()
    except Exception:
        print('\nInvalid file path for .scss!: {}'.format(filename))
        return False
    if not shortfile.endswith('.scss'):
        print('\nNot a .scss file!: {}'.format(shortfile))
        return False

    outshortfile = '{}.css'.format(shortfile[:-5])
    outfile = os.path.join(parentdir, 'css', outshortfile)
    return outfile


def get_min_targetfile(filename):
    """ Returns .min filename for a given filename. """
    fileextparts = os.path.splitext(filename)
    filebase = fileextparts[0]
    fileext = fileextparts[-1]
    if filebase.endswith('.min'):
        # Already a min file!
        print('\n.min file pass as original!: {}'.format(filename))
        return False

    minfile = '{}.min{}'.format(filebase, fileext)
    return minfile


def get_target_file(filename):
    """ Returns target file for any given file.
        Ex: get_target_file('test.js') == 'test.min.js'
            get_target_file('/sass/test.scss') == '/css/test.css'
    """

    conversionfuncs = {'.js': get_min_targetfile,
                       '.css': get_min_targetfile,
                       '.scss': get_sass_targetfile,
                       }
    fileext = os.path.splitext(filename)[-1]
    if fileext in conversionfuncs.keys():
        return conversionfuncs[fileext](filename)
    else:
        print('\nInvalid file extension '
              'for get_target_file()!: {}'.format(filename))
        return False


def is_modified(filename):
    """ Returns true if the main file has been modified,
        but the target (.min, or .css for sass) has not.
    """
    global MASTER_SASS_CHECKED, MASTER_SASS_MODIFIED, MASTER_SASS_MODTIME
    # If this is a .scss file and the master file changed,
    # we will force update it.
    if filename.endswith('.scss') and MASTER_SASS_MODIFIED:
        return True

    # This is an original file, grab the min filename
    # Grab converted filename for scss files..
    targetfile = get_target_file(filename)
    if not targetfile:
        # Unable to determine target file! (force skip)
        print('\nUnable to determine target file '
              'in is_modified()!: {}'.format(filename))
        return False

    if not os.path.isfile(targetfile):
        # No target file, has never been created. (force update)
        print('\nNew file: {}'.format(filename))
        return True

    # Get master sass modification time
    # (if this is a scss file, and it has not already been set)
    if filename.endswith('.scss') and (not MASTER_SASS_CHECKED):
        try:
            MASTER_SASS_MODTIME = os.path.getmtime(MASTER_SASS_FILE)
        except Exception as ex:
            print('\nUnable to stat master sass file: '
                  '{}\n{}'.format(MASTER_SASS_FILE, ex))
        # Either we got the time, or it errored, we won't check again.
        MASTER_SASS_CHECKED = True

    # Have original and terget, calculate modified times.
    try:
        originalmod = os.path.getmtime(filename)
    except Exception as ex:
        print('\nUnable to stat file: {}\n{}'.format(filename, ex) +
              '\nFile will be built..')
        return True
    try:
        targetmod = os.path.getmtime(targetfile)
    except Exception as ex:
        print('\nUnable to stat file: {}\n{}'.format(targetfile, ex) +
              '\nFile will be built..')
        return True

    # Check sass files against master sass file..
    if (filename.endswith('.scss') and
       MASTER_SASS_CHECKED and
       (MASTER_SASS_MODTIME > -1)):
        if MASTER_SASS_MODTIME > targetmod:
            MASTER_SASS_MODIFIED = True
            print('\n* Master SASS file was modified,'
                  '\n* All SASS files will be updated.')
            # Force update if master was modified.
            return True

    # Check original file against target..
    if originalmod > targetmod:
        # Original is newer than the target...
        return True

    # target is newer than the original
    return False


def is_skip_file(filename, **kwargs):
    """ Determines if this file should be built using included and
        filtered strings.
        Returns tuple of:
            (Boolean-Skip-File, 'Reason for skipping or not skipping')
        The SKIP_REASON_TABLE is global so it doesn't have to create it on
        every file check.

        Keyword Arguments:
            included   : List of strings that mark a file included, or None.
            filtered   : List of strings that mark a file filtered, or None.
            forced     : Force files to not be skipped if True.
            matchpath  : Strings match against the full path if True.
    """
    # Get kw arguments...
    included = kwargs.get('included', None)
    filtered = kwargs.get('filtered', None)
    forced = kwargs.get('forced', False)
    matchpath = kwargs.get('matchpath', False)

    reason = 'passed'
    # Check default filters first.
    for defaultstr in DEFAULT_FILTERS:
        if defaultstr in filename:
            return True, SKIP_REASON_TABLE['defaultfiltered']
    # Except for default filters, forced will always return False (don't skip)
    if forced:
        return False, 'forced'

    skipfile = False

    if matchpath:
        # Match included/filtered with the whole path.
        filenameshort = filename
    else:
        # Get short name for searching included/filtered strings.
        filenameshort = os.path.split(filename)[1]

    if included:
        # Check to see if this file should be included.
        for includestr in included:
            if not includestr in filenameshort:
                reason = SKIP_REASON_TABLE['notincluded']
                skipfile = True
                break

    if filtered:
        # Check to make sure this file isn't being filtered
        # (will override the included)
        for filterstr in filtered:
            if filterstr in filenameshort:
                reason = SKIP_REASON_TABLE['filtered']
                skipfile = True
                break

    # Get last modified time (if this file isn't already being skipped)...
    if not skipfile:
        if not is_modified(filename):
            # File has not been modified, we will skip it.
            reason = SKIP_REASON_TABLE['modifiedtime']
            skipfile = True

    return skipfile, reason


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


def parse_modtime(s, default=30):
    """ Parses the --modtime arg, returns the default MIN_TIME on failure.
        This arg has been deprecated!
    """

    if not s:
        return default

    try:
        ftime = float(s)
        return ftime
    except:
        print('\nInvalid value for --modtime!: '
              '{}\n..using the default.'.format(s))
        return default


def print_buildstatus(**kwargs):
    """ Print status of build flags..
        Keyword Arguments:
            method     : String to identify this type of build
                         ('CSS', 'JS', 'All', etc.)
            filecount  : Length of file list (not always used or available.)
            ...for the rest see walk_files_byext()
    """
    # Get keyword arguments.
    included = kwargs.get('included', None)
    filtered = kwargs.get('filtered', None)
    forced = kwargs.get('forced', False)
    matchpath = kwargs.get('matchpath', False)
    # Special keyword arg for this function only..
    method = kwargs.get('method', 'All')
    filecount = kwargs.get('filecount', None)

    if included:
        includestr = ' '.join(['\'{}\''.format(s) for s in included])
    else:
        includestr = 'All'
    if filtered:
        filterstr = ' '.join(['\'{}\''.format(s) for s in filtered])
    else:
        filterstr = 'None'
    if forced and included:
        includestr += ' (--all is being used, these includes don\'t matter!)'
    if filtered:
        if forced:
            filterstr += (' (--all is being used, '
                          'non-default filters don\'t matter!)')
    else:
        filterstr += ' (default filters only)'

    if forced:
        forcedstr = ('True (all files will be built, '
                     'filters/includes are ignored.)')
    else:
        forcedstr = 'False'
    if matchpath:
        matchpathstr = 'True (full paths will be matched by filters/includes'
    else:
        matchpathstr = 'False'

    filecountstr = '{} '.format(str(filecount)) if filecount else ''
    debugstr = 'On (Nothing will be built.)' if DEBUG else 'Off'
    print(' Build started: {}{} files'.format(filecountstr, method))
    print('      Included: {}'.format(includestr))
    print('      Filtered: {}'.format(filterstr))
    print('        Forced: {}'.format(forcedstr))
    print('    Match Path: {}'.format(matchpathstr))
    print('    Debug Mode: {}'.format(debugstr))
    print('\n')


def trim_filename(s, maxlength=40):
    """ Trim a long filename down to maxlength chars with '...' prepended.
        ...for printing status.
    """

    # Account for '...' or extra spaces...
    maxlength = maxlength - 3
    if len(s) > maxlength:
        # Shorten this name, prepend '...'
        return '...{}'.format(s[-maxlength:])
    else:
        # Space indent this short filename. (Account for '...')
        spacelen = (len(s) - maxlength) + 3
        return '{}{}'.format((' ' * spacelen), s)


def walk_files_byext(exts, **kwargs):
    """ Retrieve all static files by extension.
        Yields one filename at a time.
        Arguments:
            exts       : File must end with 'ext' to count.
                         (Can be a list of extensions)

        Keyword Arguments:
            filtered   : List of strings that will exclude a file.
                         Example: get_files_byext('.js', ['min'])
                                  # Filters out .min.js files.
            included   : List of string that will include a file.
                         (exclude takes precedence)
            forced     : If True, all files will be built no matter what the
                         modified status is.
            matchpath  : If True, included/filtered matches against the whole
                         file path, not just the filename.
                         Ex: get_file_byext('.js',
                                            included=['admin'], matchpath=True)
                             ...this will match all the files in any /admin
                             directory.
            silent     : If silent, don't print anything ever
                         (overrides global DEBUG (--debug))
    """

    included = kwargs.get('included', None)
    filtered = kwargs.get('filtered', None)
    forced = kwargs.get('forced', False)
    matchpath = kwargs.get('matchpath', False)
    silent = kwargs.get('silent', False)

    def _print(s):
        if not silent:
            print(s)

    def is_extension(f):
        """ returns True if file has extension in exts. """

        return (f[-3:] in exts) or (f[-4:] in exts) or (f[-5:] in exts)

    if not isinstance(exts, (list, tuple, set)):
        exts = [exts]

    for root, dirs, files in os.walk(settings.BASE_DIR):  # @UnusedVariable

        # Only look in static dirs.
        if not '/static' in root:
            continue

        for filename in files:
            # Only get files with matching extension.
            if is_extension(filename):
                fullpath = os.path.join(root, filename)
                skipfile, skipreason = is_skip_file(fullpath,
                                                    included=included,
                                                    filtered=filtered,
                                                    forced=forced,
                                                    matchpath=matchpath)
                if skipfile:
            # This file will be skipped.
                    if DEBUG:
                        _print('    Skip file {} : {}'.format(skipreason,
                                                              filename))
                else:
                    # File will be processed
                    if DEBUG:
                        _print('    Found file {}: {}'.format(skipreason,
                                                              filename))
                    yield fullpath

    return


class ToolNotFound(Exception):
    pass


# START OF SCRIPT
if __name__ == '__main__':
    mainargd = docopt(usage_str, version=_VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)
