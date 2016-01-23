#!/usr/bin/pypy
# -*- coding: utf-8 -*-

"""searchpat.py

   Uses stackless to search for regex patterns in files or stdin input.
   There are seperate tasks for grabbing filenames and saerching content/name.

   Gets faster times with stackless vs. pypy.
   ...if you can 'import stackless' then it should work.

   Before this script blew up several experiments were done to find the fastest
   method for walking a directory and "grepping" it's files.
   Out of normal os.walk, threading, multiprocessing, pypy, and stackless
   channels, the stackless channels were always faster when searching large
   directory trees. After the basic method was decided, many features were
   added (all while still experimenting with execution speed). This script is
   a mess of experiments with some features tacked on in a sub-optimal way.
   It provides defaults that I like, and features that could honestly be
   obtained from other commands, but with arguments that I like.
   For what it's worth, I still use find, grep, ag, and others on a regular
   basis, but %95 of the time this little 'searchpat' script gives me exactly
   what I need in the format that I want.

   -Christopher Welborn 2013? (date added 10-4-2015)
"""
from __future__ import print_function
import datetime    # for basic timing of things
import magic       # for determining binary/text files.
import os          # file/dir io
import re          # pattern matching
import subprocess  # shell bash code
import sys         # args, python version

# Helper for sending stdin to subprocess.Popen
from tempfile import SpooledTemporaryFile

try:
    import stackless
except ImportError as exnostackless:
    print('\nThis script requires stackless-python, or stackless pypy!\n')
    print('Error:\n{}\n'.format(exnostackless))
    sys.exit(1)

# Docopt for arg parsing. :)
from docopt import docopt

# App Info
NAME = 'SearchPat'
VERSION = '3.6.2'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
# Save actual script filename, and use it as the name in help.
SCRIPTFILE = os.path.split(sys.argv[0])[1]
SCRIPTNAME = os.path.splitext(SCRIPTFILE)[0]

# Default file types to search if --all and --types are not used.
DEFAULT_FILE_EXTS = {
    # Extension: (name, grouping1, grouping2, etc.)
    '.bash': ('bash', 'shell'),
    '.c': ('c',),
    '.cs': ('c#', 'csharp'),
    '.cpp': ('c++', 'cpp'),
    '.css': ('css', 'web'),
    '.h': ('c headers', 'c', 'headers', 'cheaders'),
    '.hpp': ('c++ headers', 'c++', 'cpp', 'headers', 'c++headers'),
    '.htm': ('html', 'web'),
    '.html': ('html', 'web'),
    '.hs': ('haskell',),
    '.js': ('javascript', 'js', 'web'),
    '.json': ('json', 'web'),
    '.log': ('log', 'text'),
    '.md': ('markdown', 'text'),
    '.pl': ('perl', 'pl'),
    '.py': ('python', 'py'),
    '.rs': ('rust',),
    '.rst': ('rest', 'text'),
    '.scss': ('sass', 'web', 'css'),
    '.sh': ('shell', 'bash', 'ksh', 'zsh'),
    '.tex': ('tex', 'text'),
    '.txt': ('text',),
    '.xml': ('xml', 'web'),
}
DEFAULT_FILETYPES = tuple(sorted(DEFAULT_FILE_EXTS.keys()))
# File types grouped by name, with a list of file extensions.
FILETYPES = {}
for ext, names in DEFAULT_FILE_EXTS.items():
    for n in names:
        existing = FILETYPES.get(n, None)
        if existing is None:
            FILETYPES[n] = {ext}
        else:
            FILETYPES[n].add(ext)


def filler_run(startpath, filetypes, channel_=None, excludepat=None):
    """ task to start finding files,
        sends to searcher_run tasklet via channel.

        This is used in get_dir_matches() to get filenames to search.

        Arguments:
            startpath  : Starting dir to get file names from.
            filetypes  : File types to search.
            channel_   : Stackless channel for communication.
            excludepat : Compiled regex, file names that match are excluded.
    """
    for fullpath in iter_walkdir(startpath, filetypes, excludepat=excludepat):
        channel_.send(fullpath)

    channel_.send('!FINISHED')


def searcher_run(searchpat, kw_args, **kwargs):  # noqa
    """ Receive file names from filler tasklet, and search them.
        Arguments:
            searchpat   : Precompiled regex pattern to search with.
            kw_args     : kwargs for get_file_matches/get_filename_matches

        Keyword Arguments:
            matches     : MatchesCollection to add to.
            colors      : ColorCodes() class to use (or None for no color)
            channel_    : Channel for task communications.
            names_only  : Search file names only, not content.
            no_lines    : Print file names only, not matching lines.
            shell_code  : Bash code to run against each file name, when
                          no_lines is used. {} will be replaced with the file
                          name. If no {} is present, it will be appended to the
                          code. {f}, or {fname} may also be used to replace
                          more than one occurrence.
            urlmode     : Print names as urls.
    """
    matches = kwargs.get('matches', None)
    colors = kwargs.get('colors', None)
    channel_ = kwargs.get('channel_', None)
    names_only = kwargs.get('names_only', False)
    no_lines = kwargs.get('no_lines', False)
    shell_code = kwargs.get('shell_code', None)
    urlmode = kwargs.get('urlmode', False)
    if shell_code:
        if '{}' in shell_code:
            codefmt = shell_code.format
        elif '{f}' in shell_code:
            codefmt = lambda fname: shell_code.format(f=fname)
        elif '{fname}' in shell_code:
            codefmt = lambda fname: shell_code.format(fname=fname)
        else:
            codefmt = lambda fname: ' '.join((shell_code, fname))
    else:
        codefmt = None

    namefmt = 'file://{}'.format if urlmode else '{}'.format
    if names_only:
        # Searching file names only, not content.
        get_matches = get_filename_matches
        format_name = lambda s: '\n{}'.format(namefmt(s))
    else:
        # Searching content, possibly only listing names.
        get_matches = get_file_matches
        if no_lines:
            format_name = lambda s: '\n{}'.format(namefmt(s))
        else:
            format_name = lambda s: '\n{}:'.format(namefmt(s))

    # Loop until channel_ receives '!FINISHED',
    # expects data to be a valid filename.
    # searches the file, and reports matches.
    # also, updates the MatchesCollection() (matches).
    stay = True
    while stay:
        data = channel_.receive()
        if data == '!FINISHED':
            stay = False
            break

        # Search file
        filename = data
        filematch = get_matches(filename, searchpat, **kw_args)
        matches.searched += 1
        if filematch:
            # save this match for counts/info
            matches.additem(filematch)
            # print results as we go, colorize filename if applicable.
            if colors:
                filepath = colors.word(
                    filename,
                    style='bright',
                    fore='blue')
            else:
                filepath = filename

            if no_lines and shell_code:
                # Run shell code including the file name.
                out = RunProcess().shell_code(codefmt(filename))
                if out:
                    print(out)
            else:
                # Printing the file name, with or without lines.
                print(format_name(filepath))
            if not no_lines:
                # Lines are highlighted in get_file_matches()
                # if colors was passed.
                for matchline in filematch.iterlines():
                    print(matchline)


def targets_run(targets, filetypes=None, channel_=None, excludepat=None):  # noqa
    """ tasklet that sends targets to searcher_run tasklet via channel
        targets is a predetermined list of filenames.

        Arguments:
            startpath  : Starting dir to get file names from.
            filetypes  : File types to search.
            channel_   : Stackless channel for communication.
            excludepat : Compiled regex, file names that match are excluded.
    """

    if filetypes:
        # Files validated by extension (has to be found in filetypes)
        for target in targets:
            # Target is a file, and is a valid extension
            if os.path.isfile(target) and (file_ext(target) in filetypes):
                # Excludes.
                if excludepat and excludepat.search(target):
                    continue
                channel_.send(target)
            # Target is a directory, walk it.
            elif os.path.isdir(target):
                for root, dirs, files in os.walk(target):
                    # Exclude dir name also.
                    if excludepat and excludepat.search(root):
                        continue
                    for filename in files:
                        # Excludes.
                        if excludepat and excludepat.search(filename):
                            continue
                        # Check extension before sending
                        if file_ext(filename) in filetypes:
                            fullpath = os.path.join(root, filename)
                            channel_.send(fullpath)
    else:
        # ALL FILES ALLOWED
        for target in targets:
            # Excludes.
            if excludepat and excludepat.search(target):
                continue
            # Target is a file, send it.
            if os.path.isfile(target):
                channel_.send(target)
            # Target is a directory, walk it and send filenames.
            elif os.path.isdir(target):
                for root, dirs, files in os.walk(target):
                    # Exclude dirs..
                    if excludepat and excludepat.search(root):
                        continue
                    for filename in files:
                        if excludepat and excludepat.search(filename):
                            continue
                        fullpath = os.path.join(root, filename)
                        channel_.send(fullpath)

    channel_.send('!FINISHED')


def addfile_maxlen(
        info,
        text=None, lineno=None, length=None,
        maxlength=None, after=None, before=None):
    """ Add a file to MatchInfo only if max_len is not exceeded
        This is one of two methods for adding files, determined by the
        maxlength flag in get_file_matches.
    """
    if length < maxlength:
        before = (MatchLine(t, n) for n, t in before) if before else None
        after = (MatchLine(t, n) for n, t in after) if after else None
        info.lines.append(
            MatchLine(
                text=text, lineno=lineno, before=before, after=after))
    return None


def addfile_normal(
        info,
        text=None, lineno=None, length=None,
        maxlength=None, after=None, before=None):
    """ Add a file to a MatchInfo..
        This is one of two methods for adding files, determined by the
        maxlength flag in get_file_matches.
    """
    before = (MatchLine(t, n) for n, t in before) if before else None
    after = (MatchLine(t, n) for n, t in after) if after else None
    info.lines.append(
        MatchLine(
            text=text, lineno=lineno, before=before, after=after))
    return None


def file_ext(fname):
    """ Gets file extension from filename,
        If no extension is present,
        the full filename is returned without the path.
    """
    filename, extension = os.path.splitext(fname)
    return extension if extension else filename


def format_block(text, prepend=None, lstrip=False, blocksize=60, spaces=False):
    """ Format a long string into a block of newline seperated text. """
    lines = make_block(text, blocksize=blocksize, spaces=spaces)
    if prepend is None:
        return '\n'.join(lines)
    if lstrip:
        # Add 'prepend' before each line, except the first.
        return '\n{}'.format(prepend).join(lines)
    # Add 'prepend' before each line.
    return '{}{}'.format(prepend, '\n{}'.format(prepend).join(lines))


def format_nomin(s):
    """ Add the --nomin regex pattern to an existing pattern,
        Or return the --nomin pattern itself.
    """
    if s:
        return r'({})|((\.min\.(\w+)$))'.format(s)
    return r'\.min\.(\w+)$'


def get_context_after(lst, index, count, strip_=str.strip):
    """ Grabs a slice from a list (for match context)
        Arguments:
            lst    : The list to slice.
            index  : The index to start from.
            count  : The number of items to get.
        Returns a tuple of (index + 1, line)
    """
    return (
        (index + n + 2, strip_(t))
        for n, t in enumerate(
            lst[index + 1: index + count + 1])
        if t)


def get_context_before(lst, index, count, strip_=str.strip):
    """ Grabs a slice from a list, returns their indexes and lines.
        Arguments:
            lst    : The list to slice.
            index  : The index to start from.
            count  : The number of items to get.
        Returns a tuple of (index + 1, line)
    """
    return (
        (index - (count - n) + 1, strip_(t))
        for n, t in enumerate(
            lst[index - count: index])
        if t)


def get_dir_matches(startpath, searchpat, **kwargs):
    """ searches all files in a directory, uses multiple threads.
        Arguments:
            startpath     : Directory to walk for files to search.
            searchpat     : Pre-compiled regex pattern to search with.

        Keyword Arguments:
            reverse       : If True, include lines that DONT match.
                            (Default: False)
            print_status  : If True, print file name before searching.
                            (Default: False)
            filetypes     : List of file extensions to search.
                            (Default: None (all files))
            debug         : Print more info (UnicodeDecodeError right now)
            colors        : ColorCodes() class to highlight with,
                            or None for no highlighting.
            names_only    : Match against file names only, not content.
            wholepath     : Match against whole path instead of just the
                            filename. (When names_only is used.)
                            Default: False
            excludepat    : Compiled regex pattern, if a file name matches,
                            it is excluded.
            before        : Number of context lines to show before a match.
            after         : Number of context lines to show after a match.
            no_lines      : Print only file names, not matching lines.
            urlmode       : Print names as urls.
    """

    filetypes = kwargs.get('filetypes', None)
    debug = kwargs.get('debug', False)
    colors = kwargs.get('colors', None)
    names_only = kwargs.get('names_only', False)
    excludepat = kwargs.get('excludepat', None)
    no_lines = kwargs.get('no_lines', False)
    shell_code = kwargs.get('shell_code', None)
    urlmode = kwargs.get('urlmode', False)
    if debug:
        printobj(kwargs, label='get_dir_matches kwargs')

    # Communications Channel
    channel = stackless.channel()
    # Matches Collection
    matches = MatchCollection()
    # Tasks for filling filename/searching files
    fillertask = stackless.tasklet(filler_run)(  # noqa
        startpath,
        filetypes,
        channel,
        excludepat=excludepat)
    searchertask = stackless.tasklet(searcher_run)(  # noqa
        searchpat,
        kwargs,
        matches=matches,
        colors=colors,
        channel_=channel,
        names_only=names_only,
        no_lines=no_lines,
        shell_code=shell_code,
        urlmode=urlmode)
    try:
        stackless.run()
    except KeyboardInterrupt:
        print_cancelled(colors)

    if debug:
        print('\nFinished searching.')

    return matches


def get_file_matches(filename, searchpat, **kwargs):  # noqa
    """ Searches a single file for a match. returns single MatchInfo()

        Arguments:
            filename      :  File to open and search
            searchpat     :  Pre-compiled regex pattern to search with.

        Keyword Arguments:
            after         :  Number of context lines to show after a match.
            before        :  Number of context lines to show before a match.
            reverse       :  If True, return lines that DONT match.
                             (Default: False)
            reversenames  :  If True, only return file names that don't have
                             and matching lines.
                             (Defailt: False)
            maxlength     :  Exclude lines longer than maxlength.
                             (Default: 0 (no max))
            print_status  :  If True, print file name before searching.
                             (Default: False)
            debug         :  Print more info (UnicodeDecodeError right now)
            colors        :  ColorCodes() class to highlight with,
                             or None for no highlighting.
            nobinary      :  Check to see if the file is binary before opening
                             it. Binary files will be skipped. This is slower.
    """
    after = kwargs.get('after', 0)
    before = kwargs.get('before', 0)
    reverse = kwargs.get('reverse', False)
    reversenames = kwargs.get('reversenames', False)
    print_status = kwargs.get('print_status', False)
    maxlength = kwargs.get('maxlength', False)
    debug = kwargs.get('debug', False)
    colors = kwargs.get('colors', None)
    nobinary = kwargs.get('nobinary', False)

    # Skip all binary files if --excludebinary is used.
    if nobinary and is_binary(filename):
        if print_status:
            fname = '<stdin>' if filename == '-' else filename
            print('    skipped binary file: {}'.format(fname))
        return None

    # Style for highlighting matches
    highlight_args = {'style': 'bright', 'fore': 'red'}
    if print_status:
        print('    {}...'.format(filename))

    # Predetermine functions to use,
    # moves several if statements OUTSIDE of the loop.
    add_func = addfile_maxlen if maxlength else addfile_normal
    # Normal match or reverse?
    match_func = is_none if reverse else is_not_none
    # Whether or not to grab context lines.
    get_before = get_context_before if before > 0 else lambda x, y, z: None
    get_after = get_context_after if after > 0 else lambda x, y, z: None

    # preload strip()
    strip_ = str.strip
    # preload replace()
    replace_ = str.replace
    # preload searchpat.search()
    search_func = searchpat.search
    # predetermine color use
    usecolors = (colors and (not reverse))

    # Initialize blank match information.
    file_info = MatchInfo()
    # Set the filename for this matchinfo, or use 'stdin'
    file_info.filename = 'stdin' if filename == '-' else filename

    # Read file/or use stdin.
    try:
        if filename == '-':
            # Use stdin.
            filelines = sys.stdin.readlines()
        else:
            # Use a file.
            with open(filename, 'r') as fread:
                filelines = fread.readlines()
    except EnvironmentError:
        print('Can\'t read file, skipping: {}'.format(filename))
        return None
    except UnicodeDecodeError:
        if debug:
            print('Wrong encoding for file, skipping: {}'.format(filename))
        return None
    except Exception as exio:
        # General error while reading.
        print('Error reading from: {}\n{}'.format(file_info.filename, exio))
        return None

    # SEARCH FILE
    # Use indexes to track line numbers while iterating the lines.

    for lineindex, line in enumerate(filelines):
        beforelines, afterlines = None, None
        # try match
        re_match = search_func(line)
        # use the pre-determined matching function (normal/reverse)
        if not match_func(re_match):
            continue

        line = strip_(line)
        # Save the raw line length for maxlength.
        rawlen = len(line)
        # Highlight match text if ColorCodes() class was passed.
        if not reverse:
            highlight_txt = re_match.group()
            if usecolors and highlight_txt:
                line = replace_(
                    line,
                    highlight_txt,
                    colors.word(highlight_txt, **highlight_args))

        # Grab context before/after this match (if before/after was set).
        beforelines = get_before(filelines, lineindex, before)
        afterlines = get_after(filelines, lineindex, after)

        # Instead of using add_func/addfile_normal just do this:!
        # The function call takes longer than the if statement!
        # before = (MatchLine(t, n) for n, t in before) if before else None
        # after = (MatchLine(t, n) for n, t in after) if after else None
        # info.lines.append(
        #    MatchLine(
        #        text=text, lineno=lineno, before=before, after=after))

        # Add this match and all of it's info to the MatchInfo.
        add_func(
            info=file_info,
            text=line,
            lineno=lineindex + 1,
            length=rawlen,
            maxlength=maxlength,
            before=beforelines,
            after=afterlines)

    # Finished.
    matching_file = bool(file_info.lines)
    if reversenames:
        # Return the file info if no lines were found.
        matching_file = not matching_file

    return file_info if matching_file else None


def get_filename_matches(filepath, searchpat, **kwargs):
    """ Test searchpat for match against a file name.
        Is interchangeable with the get_file_matches() function.

        Arguments:
            filepath   : File name/path to match against.
            searchpat  : Compiled regex pattern to match with.

        Keyword arguments:
            reverse    : File names that don't match the pattern are a 'match'.
            wholepath  : Match against whole path instead of just the filename.
                         Default: False
            excludepat : Compiled regex pattern, if a filename matches,
                         it is excluded.
    """
    reverse = kwargs.get('reverse', False)
    wholepath = kwargs.get('wholepath', False)
    excludepat = kwargs.get('excludepat', None)

    # Use whole path or just the file name?
    filename = filepath if wholepath else os.path.split(filepath)[1]

    # Excludes.
    if excludepat and (excludepat.search(filename) is not None):
        return None

    # Get match using search pattern.
    match = searchpat.search(filename)
    if (not match) or (reverse and match):
        # Nothing returned for no match, or a match against reverse search.
        return None

    # Filename matches, build a MatchInfo object and return it.
    return MatchInfo(filename=filepath)


def get_filetype_str(filetypes, colors=None):
    """ Get a human-friendly file type string for status.
        like: '.c, .py' or 'None'
        Arguments:
            filetypes  : List of file extensions.
            colors     : ColorCodes() class to use or None for no colors.
    """
    if not filetypes:
        typestr = 'All Files'
        return colors.word(typestr, fore='blue') if colors else typestr

    if colors:
        colortypes = [colors.word(s, fore='blue') for s in filetypes]
        return ', '.join(colortypes)

    return ', '.join(filetypes)


def get_multi_matches(targets, searchpat, **kwargs):
    """ Searches multiple files/dirs passed in
        with * expansion or just repeating args
        Arguments:
            targets       : List of files/dirs to search.
            searchpat     : Pre-compiled regex pattern to search with.

        Keyword Arguments:
            reverse       : If True, include lines that DONT match.
                            (Default: False)
            print_status  : If True, print file name before searching.
                            (Default: False)
            filetypes     : List of file extensions to search
                            (Default: None (all files))
            debug         : Print more info (UnicodeDecodeError right now)
            colors        : ColorCodes() class to highlight with,
                            or None for no highlighting.
            names_only    : Match against file names only, not content.
            wholepath     : Match against whole path instead of just the
                            filename. (When names_only is used.)
                            Default: False
            excludepat    : Compiled regex pattern, if a file name matches,
                            it is excluded.
            before        : Number of context lines to show before a match.
            after         : Number of context lines to show after a match.
            no_lines      : Print only file names, not matching lines.
            urlmode       : Print names as urls.
    """

    filetypes = kwargs.get('filetypes', None)
    debug = kwargs.get('debug', False)
    colors = kwargs.get('colors', None)
    names_only = kwargs.get('names_only', False)
    excludepat = kwargs.get('excludepat', None)
    no_lines = kwargs.get('no_lines', False)
    shell_code = kwargs.get('shell_code', None)
    urlmode = kwargs.get('urlmode', False)

    if debug:
        printobj(kwargs, label='get_file_matches kwargs')

    # Communications channel (sends filenames from targettask to searcher)
    channel = stackless.channel()
    # Matches Collection (The searcher task will modify this while running.)
    matches = MatchCollection()
    # Tasks for reporting targets/searching
    targettask = stackless.tasklet(targets_run)(  # noqa
        targets,
        filetypes,
        channel,
        excludepat=excludepat)
    searchertask = stackless.tasklet(searcher_run)(  # noqa
        searchpat,
        kwargs,
        matches=matches,
        colors=colors,
        channel_=channel,
        names_only=names_only,
        no_lines=no_lines,
        shell_code=shell_code,
        urlmode=urlmode)
    try:
        stackless.run()
    except KeyboardInterrupt:
        print_cancelled(colors)

    if debug:
        print('\nFinished searching.')

    return matches


def get_target_str(target, colors=None):
    """ Get a human friendly string for status about the search target/s.
        like: '1 file' or '38 files/directories' or '../myfile.py'
        Arguments:
            target  : List of targets from command line args (argd).
            colors  : ColorCodes() class to use, or None for no color.
    """
    if len(target) == 1:
        if target[0] == '-':
            # Searching stdin only.
            return colors.word('stdin', fore='blue') if colors else 'stdin'

        # Single file or directory.
        if colors:
            return colors.word(os.path.abspath(target[0]), fore='blue')
        return os.path.abspath(target[0])

    # Multiple targets, may be files or directories
    # (could be shell-expanded *.whatever)
    lenstr = str(len(target))
    typestr = 'files/directories'
    if colors:
        lenstr = colors.word(lenstr, style='bright', fore='blue')
        typestr = colors.word(typestr, fore='blue')

    return '{} {}'.format(lenstr, typestr)


def is_binary(filename):
    """ Determine whether a file is binary or text. """
    if filename == '-':
        # stdin (magic.from_buffer doesn't always work for this)
        # This may return false positives, but it's better than skipping
        # valid files.
        return False

    path = readlink(filename)
    try:
        mimetype = magic.from_file(path, mime=True)
    except OSError:
        # This may return false negatives. Assumes errors are binary files.
        return True
    return not mimetype.startswith(b'text')


def is_none(obj):
    """ Helper for get_file_matches,
        with reverse flag it uses: match_func = is_none(match)
    """
    # This function is declared once globally,
    # instead of using a new lambda on every single file.
    return (obj is None)


def is_not_none(obj):
    """ Helper for get_file_matches,
        with no reverse flag it uses: match_func = is_not_none(match)
    """
    # This function is declared once globally,
    # instead of using a new lambda on every single file.
    return (obj is not None)


def iter_walkdir(startpath=None, filetypes=None, excludepat=None):  # noqa
    """ Iterates over os.walk starting with 'startpath'.
        If `filetypes` is given (list of extensions), files are only
        yielded when it's extension is in the list of extensions.

        Arguments:
            startpath  : Dir to walk from.
            filetypes  : List of file extensions to include.
                         (Default: None (all files))
            excludepat : Compiled regex pattern, if a file name matches,
                         it is excluded.

        Yields: A full filepath (string) as the directories are walked.
    """
    if filetypes:
        valid_types = {ext: True for ext in filetypes}
        # Walk the directory, yielding filtered file paths
        for root, dirs, files in os.walk(startpath):
            # Exclude dirs also.
            if excludepat and (excludepat.search(root) is not None):
                continue
            for filename in files:
                # Excludes.
                if excludepat and (excludepat.search(filename) is not None):
                    continue
                # Valid file extension.
                if valid_types.get(file_ext(filename), False):
                    yield os.path.join(root, filename)
    else:
        # Walk the directory, yielding ALL files
        # (it's not really good to search binary files though)
        for root, dirs, files in os.walk(startpath):
            # Exclude dirs also..
            if excludepat and (excludepat.search(root) is not None):
                continue
            for filename in files:
                # Excludes.
                if excludepat and (excludepat.search(filename) is not None):
                    continue
                # Good filename.
                yield os.path.join(root, filename)


def make_block(text, blocksize=60, spaces=False):
    """ Turns a long string into a list of lines no greater than 'blocksize'
        in length. This can wrap on spaces, instead of chars if wrap_spaces
        is truthy.
    """
    if not spaces:
        # Simple block by chars.
        return (text[i:i + blocksize] for i in range(0, len(text), blocksize))
    # Wrap on spaces..
    words = text.split()
    lines = []
    curline = ''
    for word in words:
        possibleline = ' '.join((curline, word)) if curline else word
        if len(possibleline) > blocksize:
            lines.append(curline)
            curline = word
        else:
            curline = possibleline
    if curline:
        lines.append(curline)
    return lines


def parse_filetypes(s):
    """ Parse a comma separated string of types.
        This will return a list of file extensions.
        If a named file type is used from FILETYPES (python, web, etc.),
        then it's list of extensions is added to the list.
        Returns a list on success, or None on failure.
    """
    types = []
    for typeext in s.split(','):
        typeext = typeext.strip()
        typeextlower = typeext.lower()
        if typeextlower in FILETYPES:
            # This is a named type (like python, web, etc.)
            types.extend(FILETYPES[typeextlower])
        else:
            # Normal file extension.
            types.append(typeext)
    return types if types else None


def parse_filetypes_arg(argd):
    """ Parses comma-separated list of targets
        Arguments:
            argd  : The arg dict returned by docopt.
    """
    noquotes = lambda s: s.replace('"', '').replace("'", '').replace(' ', '')

    if argd['--all']:
        # None triggers a search of all files.
        return None

    if argd['--types']:
        filetypes = noquotes(argd['--types'])
        # Doing '--types all' will trigger a search of all files.
        if filetypes.lower() == 'all':
            return None
        # User specified, names or file extesions.
        return parse_filetypes(filetypes)

    # None specified, Default file types.
    return DEFAULT_FILETYPES


def print_cancelled(colors=None):
    """ Print the 'User Cancelled' message (with or without colors) """
    cancelstr = '\nUser cancelled...\n'
    if colors:
        cancelstr = colors.word(cancelstr, style='bright', fore='red')
    print(cancelstr)


def print_fail(msg, exc=None, retcode=-1):
    """ Print a message and then exit, print exception if given.
        Arguments:
            msg      : Message to print.
            exc      : Exception() to print.
            retcode  : Exit code. Will not exit if retcode < 0.
    """

    print('\n{}'.format(msg))
    if exc:
        print('Error:\n{}'.format(str(exc)))
    if retcode > -1:
        sys.exit(retcode)


def parse_int(i, msg=None, minimum=None, maximum=None):
    """ Parse a string as an integer. Errors are fatal.
        Arguments:
            i        : A string representing an integer.
            msg      : Message to print on failure.
                       Can be a format string with one '{}' occurrence.
                       Default: 'Invalid integer: {}'
            minimum  : Set to minimum value if i < minimum.
                       Default: None
            maximum  : Set to maximum value if i > maximum.
                       Default: None
    """
    try:
        val = int(i)
    except (TypeError, ValueError):
        msg = msg or 'Invalid integer: {}'
        if '{}' in msg:
            msg = msg.format(i)
        print_fail(msg, retcode=1)

    if (minimum is not None) and (val < minimum):
        val = minimum
    if (maximum is not None) and (val > maximum):
        val = maximum
    return val


def parse_regex(s, msg=None, ignorecase=False):
    """ Parse a string into a regex pattern. Errors are fatal.
        Arguments:
            s           : String to compile.
            msg         : Message to print on failure.
                          Can be a format string with one '{}' occurrence.
                          Default: 'Invalid regex pattern: {}'
            ignorecase  : Use re.IGNORECASE to compile the pattern.
    """
    try:
        pat = re.compile(s, flags=(re.IGNORECASE if ignorecase else 0))
    except re.error as ex:
        msg = msg or 'Invalid regex pattern: {}'
        if '{}' in msg:
            msg = msg.format(s)
        print_fail(msg, exc=ex, retcode=1)
    return pat


def print_header(lbl, val):
    """ Print a status message (about search terms/settings) """
    print('{:>15} {}'.format(lbl, val))


def print_matches(
        matches,
        printlines=True, colors=None, names_only=False, urlmode=False):  # noqa
    """ Print results, from list of single MatchInfo, or MatchCollection list.
        Arguments:
            matches     : A MatchCollection() (dir search)
                          or list of 1 MatchInfo() object (single-file search).

        Keyword Arguments:
            printlines  :  If True, print every line that matched.
                           (Default: True)
            colors      :  A ColorCodes() class to highlight with,
                           or None for no highlighting.
            names_only  :  Print file names only.
            urlmode     :  Print file names as urls.
    """
    # Color theme for numbers (if colors was passed they are used)
    colors_args = {'style': 'bright', 'fore': 'green'}
    # Header/Footer for listing/finishing search details
    if names_only:
        header = '\nListing {cnt} {lbl}:'
        footer = '\nFound {cnt} {lbl}...'
    else:
        header = '\nListing {linecnt} {linelbl} in {filecnt} {filelbl}:\n'
        footer = '\nFound {linecnt} {linelbl} in {filecnt} {filelbl}...\n'

    # Helper functions
    # (used more than once, in different situations, helps to stay uniform.)
    def no_matches(cnt=None):
        """ Helper function, handles no matches found. """
        nomatchstr = '\nNo matches found.'
        if colors:
            nomatchstr = colors.word(nomatchstr, style='bright', fore='red')
        print(nomatchstr)
        if cnt is not None:
            print_searchedcount(cnt)

    def print_searchedcount(searchcount=None):
        """ Helper function, handles printing file count """
        searchedplural = 'file' if searchcount == 1 else 'files'
        searchcount = str(searchcount) if searchcount else '0'
        if colors:
            searchcount = colors.word(searchcount, **colors_args)
        print('Searched {} {}.'.format(searchcount, searchedplural))

    # Check matches object
    # (no matches object at all/no matches with files searched).
    if matches is None:
        no_matches()
        return 0
    # matches object, no results though.
    elif hasattr(matches, 'searched') and (not matches):
        no_matches(cnt=matches.searched)
        return 0

    # Total results count
    filecnt = len(matches)
    filecount = str(filecnt)
    if colors:
        filecount = colors.word(filecount, **colors_args)

    # Dir or Single File matches?
    if hasattr(matches, 'total_lines'):
        # match collection
        # (Actual MatchCollection() with helper attributes/functions)
        matches.set_urlmode(urlmode)
        linecnt = matches.total_lines()
        linecount = str(linecnt)
        if colors:
            linecount = colors.word(linecount, **colors_args)
        plural_line = 'line' if linecnt == 1 else 'lines'
        plural_file = 'file' if filecnt == 1 else 'files'

        if printlines:
            print(header.format(
                linecnt=linecount,
                linelbl=plural_line,
                filecnt=filecount,
                filelbl=plural_file))
            for match in matches.iterlines():
                print(match)
        if hasattr(matches, 'searched'):
            searchedcount = matches.searched
        else:
            searchedcount = 0
    else:
        # single file (List of MatchInfo() with len = 1)
        fileinf = matches[0]
        if fileinf is None:
            no_matches()
            return 0
        linecnt = len(fileinf.lines)
        linecount = str(linecnt)
        if colors:
            linecount = colors.word(linecount, **colors_args)
        plural_line = 'line' if linecnt == 1 else 'lines'
        plural_file = 'file'

        if printlines:
            print(header.format(
                linecnt=linecount,
                linelbl=plural_line,
                filecnt=filecount,
                filelbl=plural_file))
            singlefilename = matches[0].filename
            if colors:
                singlefilename = colors.word(singlefilename,
                                             style='bright',
                                             fore='blue')
            print('{}{} : '.format(
                'file://' if urlmode else '',
                singlefilename))
        for lineinf in matches[0].iterlines():
            print(lineinf)
        searchedcount = 1

    # Print footer with match-count, file-count
    if names_only:
        print(footer.format(
            cnt=filecount,
            lbl=plural_file))
    else:
        print(footer.format(
            linecnt=linecount,
            linelbl=plural_line,
            filecnt=filecount,
            filelbl=plural_file))
    # Print number of files searched (with color if colors was passed)
    print_searchedcount(searchedcount)

    return 0


def print_typenames():
    """ Print all the known file types (named types), formatted. """
    print('File type names:')
    for typename in sorted(FILETYPES):
        exts = sorted(FILETYPES[typename])
        print('    {:>15}: {}'.format(typename, ', '.join(exts)))
    print('\nYou can use these names with -t as shortcuts.\n')


def print_warning(*args, **kwargs):
    """ Prints a warning.
        ...only indents text right now,
           used to override when --onlynames is used.
    """
    if not args:
        return None
    pargs = list(args)
    pargs[0] = '    {}'.format(pargs[0])
    print(*pargs, **kwargs)


def printdebug(*args, **kwargs):
    """ Just a debug print. Easily searched and replaced/deleted. """
    print(*args, **kwargs)


def printobj(obj, indent=0, label=None):
    """ Debug print an object. It just pretty prints dicts/list/tuples. """
    if label:
        print('{}:'.format(label))
        indent += 4

    space = ' ' * indent
    if isinstance(obj, dict):
        for k in sorted((str(ky) for ky in obj)):
            v = obj[k]
            if isinstance(v, dict):
                print('{}{:<12}'.format(space, k))
                printobj(v, indent=indent + 4)
            elif isinstance(v, (list, tuple)):
                print('{}{:<12}'.format(space, k))
                printobj(v, indent=indent + 4)
            else:
                print('{}{:<12}: {}'.format(space, k, v))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            print('{}{}'.format(space, item))
    else:
        print('{}{}'.format(space, obj))


def readlink(path, parentdir=None):
    """ Read all symlinks until the end target is reached. """
    basedir, _ = os.path.split(path)
    try:
        linkto = os.readlink(path)
        fullpath = os.path.abspath(os.path.join(basedir, linkto))
    except OSError:
        return path if not parentdir else os.path.join(parentdir, path)
    return readlink(fullpath, parentdir=basedir)


# MAIN ENTRY POINT FUNCTION
def main(argd):  # noqa
    """ main entry-point for searchpat, expects argument dict from docopt. """
    # Get ColorCodes() if applicable (automatic --nocolors if piping output)
    if argd['--nocolors'] or (not sys.stdout.isatty()):
        colors = None
    else:
        colors = ColorCodes()

    if argd['--typenames']:
        # Just list the common file types and exit.
        print_typenames()
        return 0

    # Get target file/dir/multiple files (defaults to cwd)
    target = argd['<target>'] or [os.getcwd()]

    # Get search term, compile it as a regex pattern
    searchpat = parse_regex(
        argd['<searchterm>'],
        'Invalid search term: {}',
        ignorecase=argd['--ignorecase'])

    # Get exclude pattern, compile it as a regex pattern.
    # Add the --nomin pattern if needed.
    excludepat = None
    if argd['--nomin']:
        excludestr = format_nomin(argd['--exclude'])
    else:
        excludestr = argd['--exclude']

    if excludestr:
        excludepat = parse_regex(
            excludestr,
            'Invalid exclude pattern: {}')

    # Get maximum length, make sure it's a valid integer.
    maxlength = parse_int(
        argd['--maxlength'] or 0,
        'Invalid max length: {}',
        minimum=0)

    # Get context numbers.
    contextbefore = parse_int(
        argd['--context'] or (argd['--before'] or 0),
        'Invalid number for context/before: {}',
        minimum=0)

    contextafter = parse_int(
        argd['--context'] or (argd['--after'] or 0),
        'Invalid number for context/after: {}',
        minimum=0)

    # Colorize search type info, or use normal strings
    targetstr = get_target_str(target, colors=colors)

    reversestr = '*Reverse searching, looking for lines that don\'t match.'
    reversenamestr = (
        '*Reverse name searching, looking for files without a match.')
    reversefullstr = (
        '*Reverse, and reverse-name used. This will only find empty files!')

    searchterm = searchpat.pattern
    excludeterm = getattr(excludepat, 'pattern', 'None')
    maxlengthstr = str(maxlength)
    if colors:
        searchterm = colors.word(searchterm, fore='blue')
        reversestr = colors.word(reversestr, fore='red')
        reversenamestr = colors.word(reversenamestr, fore='red')
        reversefullstr = colors.word(reversefullstr, fore='red')
        excludeterm = colors.word(excludeterm, fore='blue')
        maxlengthstr = colors.word(maxlengthstr, fore='blue')

    # Disable header printing when --onlynames is used.
    # TODO: Refactor --onlynames for less of a hack.
    if argd['--onlynames']:
        global print_header, print_warning
        print_header = lambda s, s2: None
        print_warning = lambda s: None

    # Print header
    print_header('Searching:', targetstr)
    print_header('Pattern:', searchterm)

    if excludepat:
        print_header('Exclude:', excludeterm)
    if maxlength > 0:
        print_header('Max Length:', maxlengthstr)
    # Start time for search
    starttime = datetime.datetime.now()

    # Which search type is needed?
    if len(target) == 1 and (os.path.isfile(target[0]) or target[0] == '-'):
        # Single File Search / STDIN Search --------------------------------

        # Reverse warnings.
        if argd['--reverse'] and argd['--reversenames']:
            print_warning(reversefullstr)
        elif argd['--reverse']:
            print_warning(reversestr)
        elif argd['--reversenames']:
            print_warning(reversenamestr)

        if argd['--filenames']:
            # Only matching against the filename.
            if target[0] == '-':
                print_fail('Matching stdin as a filename!', retcode=1)

            matches = [
                get_filename_matches(
                    target[0],
                    searchpat,
                    reverse=argd['--reverse'],
                    debug=argd['--debug'],
                    wholepath=argd['--wholepath'],
                    excludepat=excludepat,
                    colors=colors)
            ]
        else:
            # Matching against a single file's content.
            if excludepat:
                msg = '--exclude will not work on a single file!'
                if colors:
                    msg = colors.word(msg, fore='red', style='bright')
                print(msg)

            matches = [
                get_file_matches(
                    target[0],
                    searchpat,
                    reverse=argd['--reverse'],
                    reversenames=argd['--reversenames'],
                    debug=argd['--debug'],
                    colors=colors,
                    maxlength=maxlength,
                    before=contextbefore,
                    after=contextafter,
                    nobinary=argd['--excludebinary'])
            ]

        # Matches are printed after searching this single file
        printmatchlines = True

    elif len(target) == 1 and os.path.isdir(target[0]):
        # Directory Search --------------------------------------------------
        # Get filetypes to search.
        filetypes = parse_filetypes_arg(argd)
        # TODO:FORMAT THIS CODE BETTER, trimming to < 79 chars made it ugly!
        filetypes = sorted(filetypes) if filetypes else None
        filetypestr = get_filetype_str(filetypes, colors=colors)
        print_header('File Types:', filetypestr)
        # Reverse notify
        if argd['--reverse'] and argd['--reversenames']:
            print_warning(reversefullstr)
        elif argd['--reverse']:
            print_warning(reversestr)
        elif argd['--reversenames']:
            print_warning(reversenamestr)

        # Do the search
        matches = get_dir_matches(
            target[0],
            searchpat,
            reverse=argd['--reverse'],
            reversenames=argd['--reversenames'],
            filetypes=filetypes,
            debug=argd['--debug'],
            colors=colors,
            names_only=argd['--filenames'],
            wholepath=argd['--wholepath'],
            excludepat=excludepat,
            maxlength=maxlength,
            before=contextbefore,
            after=contextafter,
            nobinary=argd['--excludebinary'],
            no_lines=argd['--onlynames'],
            shell_code=argd['--shellcode'],
            urlmode=argd['--urlnames']
        )

        # Matches are printed as they are found, per file
        printmatchlines = False
    elif len(target) > 1:
        # Multiple Targets Search -------------------------------------------
        # Reverse notify
        if argd['--reverse'] and argd['--reversenames']:
            print_warning(reversefullstr)
        elif argd['--reverse']:
            # Notify about reverse searching
            print_warning(reversestr)
        elif argd['--reversenames']:
            print_warning(reversenamestr)

        # Get file types to filter
        filetypes = parse_filetypes_arg(argd)
        filetypestr = get_filetype_str(filetypes, colors=colors)
        print_header('File Types:', filetypestr)
        # Do the search
        matches = get_multi_matches(
            target,
            searchpat,
            reverse=argd['--reverse'],
            reversenames=argd['--reversenames'],
            filetypes=filetypes,
            debug=argd['--debug'],
            colors=colors,
            names_only=argd['--filenames'],
            wholepath=argd['--wholepath'],
            excludepat=excludepat,
            maxlength=maxlength,
            before=contextbefore,
            after=contextafter,
            nobinary=argd['--excludebinary'],
            no_lines=argd['--onlynames'],
            shell_code=argd['--shellcode'],
            urlmode=argd['--urlnames']
        )
        # Matches are printed as they are found, per file
        printmatchlines = False
    else:
        # No target?
        if len(target) == 1:
            targets = target[0]
        else:
            targets = '\n{}'.format('\n'.join(targets))
            if len(targets) > 100:
                targets = targets[:100]
        print_fail('Invalid file/dir given!: {}'.format(targets), retcode=1)

    # Finished running, figure timed results.
    runtime = (datetime.datetime.now() - starttime).total_seconds()

    if argd['--onlynames']:
        ret = 0
    else:
        # Print header/footer and lines of applicable
        ret = print_matches(
            matches,
            printlines=printmatchlines,
            colors=colors,
            names_only=argd['--filenames'],
            urlmode=argd['--urlnames'])

        # Print run time
        runtime = '{:0.3f}'.format(runtime)
        if colors:
            runtime = colors.word(runtime, style='bright', fore='cyan')
        print('({} seconds)'.format(runtime))

    return ret


class ColorCodes(object):

    """ This class colorizes text for an ansi terminal.
        Inspired by Colorama (though very different)
    """

    def __init__(self):
        # Names and corresponding code number
        namemap = (
            ('black', 0),
            ('red', 1),
            ('green', 2),
            ('yellow', 3),
            ('blue', 4),
            ('magenta', 5),
            ('cyan', 6),
            ('white', 7)
        )
        self.codes = {'fore': {}, 'back': {}, 'style': {}}
        # Set codes for forecolors (30-37) and backcolors (40-47)
        for name, number in namemap:
            self.codes['fore'][name] = str(30 + number)
            self.codes['back'][name] = str(40 + number)
        # Set reset codes for fore/back.
        self.codes['fore']['reset'] = '39'
        self.codes['back']['reset'] = '49'

        # Map of code -> style name/alias.
        stylemap = (
            ('0', ['reset', 'reset_all']),
            ('1', ['bright', 'bold']),
            ('2', ['dim']),
            ('3', ['italic']),
            ('4', ['underline', 'underlined']),
            ('5', ['flash']),
            ('7', ['highlight', 'hilight', 'hilite']),
            ('22', ['normal', 'none'])
        )
        # Set style codes.
        for code, names in stylemap:
            for alias in names:
                self.codes['style'][alias] = code

    def color_code(self, style=None, back=None, fore=None):
        """ Return the code for this style/color
            Right now if fore is a reset, it cancels out the previous codes.
            ...same with back. I fixed this in a another implementation,
               and will get around to it when I can with this one.
        """

        codestr = ''
        if style and (style in self.codes['style'].keys()):
            codestr += '\033[{}m'.format(self.codes['style'][style])
        if back and (back in self.codes['back'].keys()):
            codestr += '\033[{}m'.format(self.codes['back'][back])
        if fore and (fore in self.codes['fore'].keys()):
            codestr += '\033[{}m'.format(self.codes['fore'][fore])

        return codestr

    def colorize(self, text, style=None, back=None, fore=None):
        """ Return text colorized.
            fore,back,style  : Name of fore or back color, or style name.
        """
        return '{codes}{txt}'.format(codes=self.color_code(style=style,
                                                           back=back,
                                                           fore=fore),
                                     txt=text)

    def colorizepart(self, text, style=None, back=None, fore=None):
        """ Same as colorize, but adds a style->reset_all after it. """
        colorized = self.colorize(text, style=style, back=back, fore=fore)
        s = '{colrtxt}{reset}'.format(colrtxt=colorized,
                                      reset=self.color_code(style='reset_all'))
        return s

    def word(self, *args, **kwargs):
        """ Shorthand for colorizepart. """
        return self.colorizepart(*args, **kwargs)


class Output(object):

    """ Class to hold process output, distinguishable from an ErrorOutput.
        Used by RunProcess().
    """

    def __init__(self, lines, proc=None):
        self.lines = lines
        self.data = '\n'.join(lines).strip('\n') if lines else ''
        if proc is None:
            self.exitcode = None
        else:
            self.exitcode = proc.wait()

    def __bool__(self):
        return bool(self.data)

    def __str__(self):
        return self.data


class ErrorOutput(Output):

    """ Class to hold process output, distinguishable from a normal Output.
        Used by RunProcess().
    """
    pass


class MatchLine(object):

    """ single line in a MatchInfo() """
    __slots__ = ('after', 'before', 'lineno_len', 'lineno', 'text')
    # Level of indention for line numbers when represented as a string.
    # (if the len(str(lineno)) > lineno_len formatting will be wrong!)
    lineno_len = 4

    def __init__(self, text=None, lineno=None, before=None, after=None):
        # Lines of context after this match line (iterable of MatchLine).
        self.after = after
        # Lines of context before this match line (iterable of MatchLine).
        self.before = before

        # Text for this line match.
        self.text = text
        # Line number or this line match.
        self.lineno = lineno

    def __str__(self):
        # trim tabs/spaces characters, replaces with '...'
        # (for str() and repr() only)
        if self.text.startswith(' ') or self.text.startswith('\t'):
            stext = '... ' + self.text.strip()
        else:
            stext = self.text
        linestr = str(self.lineno).rjust(MatchLine.lineno_len)
        lines = []
        if self.before:
            # Context before
            lines.extend((
                '',
                '\n'.join((str(l) for l in self.before))))

        lines.append('  {}: {}'.format(linestr, stext))
        if self.after:
            # Context after
            lines.append('\n'.join((str(l) for l in self.after)))
            if not self.before:
                # Ensure a blank line because it gets messy.
                lines.append('')

        return '\n'.join(lines)

    def __repr__(self):
        return self.__str__()


class MatchInfo(object):

    """ Filename with all MatchLines() """
    __slots__ = ('filename', 'lines')

    def __init__(self, filename=None, lines=None):
        # Filename or these matches
        self.filename = filename
        # Lines that matched (list of MatchLine)
        self.lines = [] if lines is None else lines

    def iterlines(self):
        """ iterate over lines in this match. yields strings. """
        if self.lines:
            for lineinf in iter(self.lines):
                yield lineinf
        return


class MatchCollection(object):

    """ collection of MatchInfo()
        (self.items is list of MatchInfo() with helper functions in self)
        MatchCollection ->
                           MatchInfo ->
                                         MatchLine
                                         MatchLine
                           MatchInfo ->
                                         MatchLine
    """
    __slots__ = ('items', 'searched', 'urlmode')

    def __init__(self, items=None, files_searched=0):
        self.items = [] if items is None else items
        self.searched = files_searched
        self.urlmode = False

    def __add__(self, other):
        """ Add another MatchCollection to this one. """

        if isinstance(other, MatchCollection):
            if other.searched:
                self.searched = self.searched + other.searched
            if other.items:
                self.items = self.items + other.items
        else:
            errmsg = ('{} cannot be added to a MatchCollection, '
                      'only other MatchCollections.')
            raise TypeError(errmsg.format(type(other)))
        return self

    def __len__(self):
        return len(self.items)

    def iteritems(self):
        """ iterate over MatchInfo() items """
        if not self.items:
            return

        for matchinf in iter(self.items):
            yield matchinf

    def iterlines(self):
        """ iterate over MatchInfo(), yielding filename first, then lines.
            yields strings.
        """
        fmtfilename = '\nfile://{} :'.format if self.urlmode else '\n{}'.format
        if self.items:
            for matchinf in iter(self.items):
                # start of filename
                if matchinf.lines:
                    yield fmtfilename(matchinf.filename)
                else:
                    yield fmtfilename(matchinf.filename)

                # all lines.
                if matchinf.lines:
                    for matchline in matchinf.iterlines():
                        yield '    {}'.format(matchline)
        return

    def additem(self, item):
        """ add MatchInfo() item to the collection. """
        if item is not None:
            self.items.append(item)

    def total_lines(self):
        """ calculates and returns total lines from all MatchInfo() items """
        total = 0
        items = self.items or []
        for matchinf in items:
            if matchinf.lines:
                total += len(matchinf.lines)
        return total

    def set_urlmode(self, enabled):
        self.urlmode = enabled


class RunProcess(object):

    """ Runs a process, or bash code. Returns an Output() with the stdout or
        stderr output and the exit code.
    """

    def __init__(self, cmdargs=None, stdin=None):
        self.cmdargs = cmdargs
        self.stdin = stdin

    def proc_output(self, proc):
        """ Get process output, whether its on stdout or stderr.
            Return either Output() or ErrorOutput().
            Arguments:
                proc  : a POpen() process to get output from.
        """
        # Get stdout
        outlines = []
        for rawline in iter(proc.stdout.readline, b''):
            if not rawline:
                break
            line = rawline.decode()
            outlines.append(line.strip('\n'))

        # Get stderr
        errlines = []
        for rawline in iter(proc.stderr.readline, b''):
            if not rawline:
                break
            line = rawline.decode()
            errlines.append(line.strip('\n'))

        if errlines:
            return ErrorOutput(errlines, proc=proc)

        return Output(outlines, proc=proc)

    def run(self, cmdargs=None, stdin=None):
        """ Run a process with or without some stdin input, return it's output.
            Return either an Output or ErrorOutput object.
        """

        cmdargs = cmdargs or self.cmdargs
        stdin = stdin or self.stdin

        if stdin:
            with TempInput(stdin) as stdinput:
                proc = subprocess.Popen(
                    cmdargs,
                    stdin=stdinput,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
        else:
            proc = subprocess.Popen(
                cmdargs,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        return self.proc_output(proc)

    def shell_code(self, code):
        """ Run code through bash, return an Output(). """
        return self.run(cmdargs=['bash'], stdin=code)


class TempInput(object):

    """ A file-like object to pass strings as stdin to subprocess.Popen.
        with TempInput('my stuff') as stdinput:
            p = subprocess.Popen(['echo'], stdin=stdinput)
    """

    def __init__(self, inputstr):
        self.inputstr = inputstr.encode()

    def __enter__(self):
        self.tempfile = SpooledTemporaryFile()
        self.tempfile.write(self.inputstr)
        self.tempfile.seek(0)
        return self.tempfile

    def __exit__(self, type_, value, traceback):
        self.tempfile.close()
        return False


# Amount of space before usage descriptions start.
USAGE_INDENT = 38
# Amount of space before the file types should start (makes up for 'Default: ')
USAGE_TYPES_INDENT = USAGE_INDENT + 9
# Maximum width allowed for the usage string.
USAGE_MAXWIDTH = 80
# Formatted file types string for usage.
USAGE_FILETYPES = format_block(
    ', '.join(DEFAULT_FILETYPES),
    blocksize=USAGE_MAXWIDTH - USAGE_INDENT,
    prepend=' ' * USAGE_TYPES_INDENT,
    lstrip=True,
    spaces=True)

# Usage/Help string for docopt (and whoever is reading this.)
USAGESTR = """{filename} v. {version}

    Usage:
        {filename} -h | -v
        {filename} <searchterm> [<target>...] [-A | -t <filetypes>] [options]
        {filename} -T

    Options:
        <searchterm>                : Regex to match in file or files.
        <target>                    : Target file, or directory to search in.
                                      If '-' is given as the only target,
                                      stdin will be used.
                                      Default: {cwd}
        -A,--all                    : Search all file types.
                                      (Same as '--types all')
                                      Can be slow. It searches all files,
                                      even binary files, which is not good.
        -a num,--after num          : Lines of context to show after a match.
        -b num,--before num         : Lines of context to show before a match.
        -c num,--context num        : Like using 'after' and 'before', both
                                      with the same number.
        -D,--debug                  : Print more debug info.
        -e pat,--exclude pat        : Exclude filenames with this pattern
                                      in them.
        -f,--filenames              : Match against file names only,
                                      not content.
        -h,--help                   : Show this message.
        -i,--ignorecase             : Make the search query case insensitive.
        -l n,--maxlength n          : Maximum length for each line,
                                      lines longer than this are not included.
                                      Default: 0 (no maximum length)
        -m,--nomin                  : Automatically add '\.min\.(\w+)$' to
                                      the --exclude pattern to ignore minified
                                      files.
        -n,--nocolors               : Don't use colors at all.
        -o,--onlynames              : Don't print matching lines, just file
                                      names.
        -p,--print                  : Print ALL file names before searching.
                                      (even non-matching, it's slow!)
        -r,--reverse                : Only show lines that don't match.
        -R,--reversenames           : Show names of files that don't contain
                                      a single line match.
        -s code,--shellcode code    : Run bash code on each file name,
                                      where {{}} will be replaced with the
                                      file name. {{f}} or {{fname}} may also
                                      be used to replace more than one
                                      occurrence.
                                      Can only be used with -o.
        -t <types>,--types <types>  : Only search files with these extensions.
                                      (Comma-separated list)
                                      Default: {filetypes}
        -T,--typenames              : List the default file types and names.
                                      These names can be used as shortcuts
                                      when using -t.
        -u,--urlnames               : Print file names as urls.
        -v,--version                : Show version and exit.
        -w,--wholepath              : When matching against file names only,
                                      match against the whole file path.
        -x,--excludebinary          : Search text files only. This is slower,
                                      but may be useful when searching ALL
                                      files in a directory.

    Notes:
        Shell-expansion, --types, and recursing sub-directories:
            By default, if <target> is a directory, or contains a directory,
            any sub-directories of the target will be searched. If no target
            is specified, the current directory is the target.
            You can override this behaviour by using expansion to search only
            certain files in the current directory.
            Examples:
                {filename} 'foo' == {filename} 'foo' *
                ...since directories are expanded with *
                   both recurse into sub-directories.

                {filename} 'foo' * --types .py != {filename} 'foo' *.py
                ...all sub-directories will be included in *
                   but only .py files are searched,
                   where *.py usually excludes sub-directories.

                {filename} 'foo' *.py --types .txt == Nothing.
                ...all .py files will be sent to {filename},
                   but only .txt will be searched.

            If {filename} sees a directory in the <target>,
            it walks all sub-directories of it.

        Stackless:
            This script is setup to run with stackless-python
            (/usr/bin/stackless), but you could probably use any python
            executable that will successfully do 'import stackless'.

""".format(filename=SCRIPTFILE,
           version=VERSION,
           filetypes=USAGE_FILETYPES,
           cwd=os.getcwd())


# START OF SCRIPT
if __name__ == '__main__':
    # Parse args, exit on usage failure.
    main_argd = docopt(USAGESTR, version=VERSIONSTR)
    # Go.
    try:
        main_ret = main(main_argd)
    except KeyboardInterrupt:
        # This still happens when not using stackless (single-file searches).
        if main_argd['--nocolors'] or (not sys.stdout.isatty()):
            colors = None
        else:
            colors = ColorCodes()
        print_cancelled(colors)
        main_ret = 2

    sys.exit(main_ret)
