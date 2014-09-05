#!/usr/bin/stackless
# -*- coding: utf-8 -*-

"""searchpat.py

   Uses stackless to search for regex patterns in files or stdin input.
   There are seperate tasks for grabbing filenames and saerching content/name.

   Gets faster times with stackless vs. pypy.
   ...if you can 'import stackless' then it should work.

   -Christopher Welborn
"""

import datetime    # for basic timing of things
import os          # file/dir io
import re          # pattern matching
import sys         # args, python version

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
VERSION = '3.5.2-4'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
# Save actual script filename, and use it as the name in help.
SCRIPTFILE = os.path.split(sys.argv[0])[1]
SCRIPTNAME = os.path.splitext(SCRIPTFILE)[0]

# Default file types to search if --all and --types are not used.
DEFAULT_FILE_EXTS = {
    '.c': 'c',
    '.cpp': 'c++',
    '.css': 'css',
    '.h': 'c headers',
    '.hpp': 'c++ headers',
    '.htm': 'html',
    '.html': 'html',
    '.hs': 'haskell',
    '.js': 'javascript',
    '.json': 'json',
    '.log': 'log',
    '.md': 'markdown',
    '.pl': 'perl',
    '.py': 'python',
    '.rst': 'rest',
    '.scss': 'sass',
    '.sh': 'bash/shell',
    '.tex': 'tex',
    '.txt': 'text',
    '.xml': 'xml',
}
DEFAULT_FILETYPES = tuple(sorted(DEFAULT_FILE_EXTS.keys()))

# Usage/Help string for docopt (and whoever is reading this.)
usage_str = """{filename} v. {version}

    Usage:
        {filename} -h | -v
        {filename} <searchterm> [<target>...] [-a | -t <filetypes>] [options]

    Options:
        <searchterm>                : Regex to match in file or files.
        <target>                    : Target file, or directory to search in.
                                      If '-' is given as the only target,
                                      stdin will be used.
                                      Default: {cwd}
        -a,--all                    : Search all file types.
                                      (Same as '--types all')
                                      Can be slow, searches all files, even
                                      binary files, which is not good.
        -d,--debug                  : Print more debug info.
        -e pat,--exclude pat        : Exclude filenames with this pattern
                                      in them.
        -f,--filenames              : Match against file names only,
                                      not content.
        -h,--help                   : Show this message.
        -l n,--maxlength n          : Maximum length for each line,
                                      lines longer than this are not included.
                                      Default: 0 (no maximum length)
        -n,--nocolors               : Don't use colors at all.
        -p,--print                  : Print ALL file names before searching.
                                      (even non-matching, it's slow!)
        -t <types>,--types <types>  : Only search files with these extensions.
                                      (Comma-separated list)
                                      Default: {filetypes}
        -r,--reverse                : Only show files that don't match.
        -v,--version                : Show version and exit.
        -w,--wholepath              : When matching against file names only,
                                      match against the whole file path.

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
           filetypes=', '.join(DEFAULT_FILETYPES),
           cwd=os.getcwd())


class MatchLine():

    """ single line in a MatchInfo() """
    # Level of indention for line numbers when represented as a string.
    # (if the len(str(lineno)) > lineno_len formatting will be wrong!)
    lineno_len = 4

    def __init__(self, text=None, lineno=None):
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
        return linestr + ': ' + stext

    def __repr__(self):
        return self.__str__()


class MatchInfo():

    """ Filename with all MatchLines() """

    def __init__(self, filename=None, lines=None):
        # Filename or these matches
        self.filename = filename
        # Lines that matched (list of MatchLine)
        self.lines = [] if lines is None else lines

    def iterlines(self):
        """ iterate over lines in this match. yields strings. """
        if self.lines:
            for lineinf in iter(self.lines):
                yield str(lineinf)
        return

    def addline(self, text, lineno=-1):
        """ add a line to this match, with optional lineno. """
        self.lines.append(MatchLine(text, lineno))

    def addif(self, condition, text, lineno=-1):
        """ add a line with optional lineno, only if condition is Truthy. """
        if condition:
            self.lines.append(MatchLine(text, lineno))


class MatchCollection():

    """ collection of MatchInfo()
        (self.items is list of MatchInfo() with helper functions in self)
        MatchCollection ->
                           MatchInfo ->
                                         MatchLine
                                         MatchLine
                           MatchInfo ->
                                         MatchLine
    """

    def __init__(self, items=None, files_searched=0):
        self.items = [] if items is None else items
        self.searched = files_searched

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
        if self.items:
            for matchinf in iter(self.items):
                # start of filename
                yield '\n' + matchinf.filename + ': '
                # all lines.
                if matchinf.lines:
                    for matchline in matchinf.iterlines():
                        yield '    ' + matchline
        return

    def additem(self, item):
        """ add MatchInfo() item to the collection. """
        if item is not None:
            self.items.append(item)

    def total_lines(self):
        """ calculates and returns total lines from all MatchInfo() items """
        total = 0
        if self.items:
            for matchinf in self.items:
                if matchinf.lines:
                    total += len(matchinf.lines)
        return total


class FileAddData(object):

    """ Holds temp data for matches being added in get_file_matches() """

    def __init__(self, info=None, raw=None, line=None, lineno=None):
        self.info = info
        self.raw = raw
        self.line = line
        self.lineno = lineno

    def __len__(self):
        """ Wrapper for len() around the actual line. """
        return len(self.raw.strip()) if self.raw else 0

    def to_tuple(self):
        return self.info, self.line, self.lineno

    def addline(self):
        self.info.addline(self.line, self.lineno)

    def addlineif(self, condition):
        if condition:
            self.addline()


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


def searcher_run(searchpat, kw_args, **kwargs):
    """ Receive file names from filler tasklet, and search them.
        Arguments:
            searchpat   : Precompiled regex pattern to search with.
            kw_args     : kwargs for get_file_matches/get_filename_matches

        Keyword Arguments:
            matches     : MatchesCollection to add to.
            colorizer   : ColorCodes() class to use (or None for no color)
            channel_    : Channel for task communications.
            names_only  : Search file names only, not content.
    """
    matches = kwargs.get('matches', None)
    colorizer = kwargs.get('colorizer', None)
    channel_ = kwargs.get('channel_', None)
    names_only = kwargs.get('names_only', False)

    # Are we searching content or names only?
    if names_only:
        get_matches = get_filename_matches
        format_name = lambda s: '\n{}'.format(s)
    else:
        get_matches = get_file_matches
        format_name = lambda s: '\n{}:'.format(s)

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
            if colorizer:
                filepath = colorizer.colorizepart(filename,
                                                  style='bright',
                                                  fore='blue')
            else:
                filepath = filename

            print(format_name(filepath))
            # Lines are highlighted in get_file_matches()
            # if colorizer was passed.
            for matchline in filematch.iterlines():
                print('    {}'.format(matchline))


def targets_run(targets, filetypes=None, channel_=None, excludepat=None):
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
                    for filename in files:
                        fullpath = os.path.join(root, filename)
                        channel_.send(fullpath)

    channel_.send('!FINISHED')


def addfile_with_maxlen(fileadd_data, maxlength=None):
    """ Add a file using FileAddData only if max_len is not exceeded
        This is one of two methods for adding files, determined by the
        maxlength flag in get_file_matches.
    """

    line, lineno = fileadd_data.line, fileadd_data.lineno
    # fileadd_data.__len__ will get the true length, minus the color-codes.
    cond = len(fileadd_data) < maxlength
    return fileadd_data.info.addif(cond, line, lineno)


def addfile_without_maxlen(fileadd_data, maxlength=None):
    """ Add a file using FileAddData.
        This is one of two methods for adding files, determined by the
        maxlength flag in get_file_matches.
    """
    return fileadd_data.info.addline(fileadd_data.line, fileadd_data.lineno)


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
            colorizer     : ColorCodes() class to highlight with,
                            or None for no highlighting.
            names_only    : Match against file names only, not content.
            wholepath     : Match against whole path instead of just the
                            filename. (When names_only is used.)
                            Default: False
            excludepat    : Compiled regex pattern, if a file name matches,
                            it is excluded.
    """

    filetypes = kwargs.get('filetypes', None)
    debug = kwargs.get('debug', False)
    colorizer = kwargs.get('colorizer', None)
    names_only = kwargs.get('names_only', False)
    excludepat = kwargs.get('excludepat', None)

    # Communications Channel
    channel = stackless.channel()
    # Matches Collection
    matches = MatchCollection()
    # Tasks for filling filename/searching files
    fillertask = stackless.tasklet(filler_run)(startpath,  # noqa
                                               filetypes,
                                               channel,
                                               excludepat=excludepat)
    searchertask = stackless.tasklet(searcher_run)(searchpat,  # noqa
                                                   kwargs,
                                                   matches=matches,
                                                   colorizer=colorizer,
                                                   channel_=channel,
                                                   names_only=names_only)
    try:
        stackless.run()
    except KeyboardInterrupt:
        if colorizer:
            cancelstr = colorizer.colorizepart('\nUser cancelled...\n',
                                               style='bright',
                                               fore='red')
        else:
            cancelstr = '\nUser cancelled...\n'
        print(cancelstr)

    if debug:
        print('\nFinished searching.')

    return matches


def get_file_matches(filename, searchpat, **kwargs):
    """ Searches a single file for a match. returns single MatchInfo()

        Arguments:
            filename      :  File to open and search
            searchpat     :  Pre-compiled regex pattern to search with.

        Keyword Arguments:
            reverse       :  If True, return lines that DONT match.
                             (Default: False)
            maxlength     :  Exclude lines longer than maxlength.
                             (Default: 0 (no max))
            print_status  :  If True, print file name before searching.
                             (Default: False)
            debug         :  Print more info (UnicodeDecodeError right now)
            colorizer     :  ColorCodes() class to highlight with,
                             or None for no highlighting.
    """
    reverse = kwargs.get('reverse', False)
    print_status = kwargs.get('print_status', False)
    maxlength = kwargs.get('maxlength', False)
    debug = kwargs.get('debug', False)
    colorizer = kwargs.get('colorizer', None)

    # Style for highlighting matches
    highlight_args = {'style': 'bright', 'fore': 'red'}
    if print_status:
        print('    {}...'.format(filename))

    # Predetermine functions to use,
    # moves several if statements OUTSIDE of the loop.
    add_func = addfile_with_maxlen if maxlength else addfile_without_maxlen
    # Normal match or reverse?
    match_func = is_none if reverse else is_not_none

    # preload strip()
    strip_ = str.strip
    # preload replace()
    replace_ = str.replace
    # preload searchpat.search()
    search_func = searchpat.search
    # predetermine color use
    usecolors = (colorizer and (not reverse))

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
    except (IOError, OSError):
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
        # try match
        re_match = search_func(line)
        # use the pre-determined matching function (normal/reverse)
        if match_func(re_match):
            # Save the raw line.
            rawline = strip_(line)
            # This might be modified using colors. (so rawline is there also)
            line = rawline
            # Highlight match text if ColorCodes() class was passed.
            if usecolors:
                text = re_match.group()
                if text:
                    line = replace_(rawline, text,
                                    colorizer.word(text, **highlight_args))

            # Stupid optimization #35:
            # use pre-determined add method (with or without max_len test)
            # file_info is modified, the line is added to it if no max_len is
            # set. If there is a max_len, it is checked before adding.
            add_func(FileAddData(info=file_info,
                                 raw=rawline,
                                 line=line,
                                 lineno=lineindex + 1), maxlength=maxlength)

    # Finished.
    if file_info.lines:
        return file_info
    else:
        # No lines, we're not saving the file's info.
        return None


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
    if excludepat and excludepat.search(filename):
        return None

    # Get match using search pattern.
    match = searchpat.search(filename)
    if (not match) or (reverse and match):
        # Nothing returned for no match, or a match against reverse search.
        return None

    # Filename matches, build a MatchInfo object and return it.
    file_info = MatchInfo()
    file_info.filename = filepath
    return file_info


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
            colorizer     : ColorCodes() class to highlight with,
                            or None for no highlighting.
            names_only    : Match against file names only, not content.
            wholepath     : Match against whole path instead of just the
                            filename. (When names_only is used.)
                            Default: False
            excludepat    : Compiled regex pattern, if a file name matches,
                            it is excluded.
    """

    filetypes = kwargs.get('filetypes', None)
    debug = kwargs.get('debug', False)
    colorizer = kwargs.get('colorizer', None)
    names_only = kwargs.get('names_only', False)
    excludepat = kwargs.get('excludepat', None)

    # Communications channel (sends filenames from targettask to searcher)
    channel = stackless.channel()
    # Matches Collection (The searcher task will modify this while running.)
    matches = MatchCollection()
    # Tasks for reporting targets/searching
    targettask = stackless.tasklet(targets_run)(targets,  # noqa
                                                filetypes,
                                                channel,
                                                excludepat=excludepat)
    searchertask = stackless.tasklet(searcher_run)(searchpat,  # noqa
                                                   kwargs,
                                                   matches=matches,
                                                   colorizer=colorizer,
                                                   channel_=channel,
                                                   names_only=names_only)
    try:
        stackless.run()
    except KeyboardInterrupt:
        if colorizer:
            cancelstr = colorizer.colorizepart('\nUser cancelled...\n',
                                               style='bright',
                                               fore='red')
        else:
            cancelstr = '\nUser cancelled...\n'
        print(cancelstr)

    if debug:
        print('\nFinished searching.')

    return matches


def is_none(obj):
    """ Helper for get_file_matches,
        with reverse flag -> match_func = is_none(match)
    """
    return (obj is None)


def is_not_none(obj):
    """ Helper for get_file_matches,
        with no reverse flag -> match_func = is_not_none(match)
    """
    return (obj is not None)


def iter_walkdir(startpath=None, filetypes=None, excludepat=None):
    """ Iterates over os.walk starting with 'startpath'.
        If filetypes is given (list of extensions), files are only
        yielded when it's extension is in the list of extensions.

        Keyword Arguments:
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
            for filename in files:
                # Excludes.
                if excludepat and excludepat.search(filename):
                    continue
                # Valid file extension.
                if valid_types.get(file_ext(filename), False):
                    yield os.path.join(root, filename)
    else:
        # Walk the directory,yielding ALL files
        # (not good to search binary files)
        for root, dirs, files in os.walk(startpath):
            for filename in files:
                # Excludes.
                if excludepat and excludepat.search(filename):
                    continue
                # Good filename.
                yield os.path.join(root, filename)


def file_ext(fname):
    """ Gets file extension from filename,
        If no extension is present, the full filename is returned.
    """

    filename, extension = os.path.splitext(fname)
    if extension:
        # Return only the extension
        return extension
    # no extension, return the filename untouched.
    return fname


def parse_filetypes_arg(originalargd):
    """ Parses comma-separated list of targets """
    noquotes = lambda s: s.replace('"', '').replace("'", '').replace(' ', '')
    if originalargd['--all']:
        # None triggers all files.
        filetypes = None
    else:
        if originalargd['--types']:
            filetypes = noquotes(originalargd['--types'])
            # Doing --types all will trigger all files.
            if filetypes.lower() in ('all',):
                filetypes = None
            else:
                filetypes = [s.strip() for s in filetypes.split(',')]
        else:
            # Default file types.
            filetypes = DEFAULT_FILETYPES

    return filetypes


def print_fail(msg, exc=None, retcode=-1):
    """ Print a message and then exit, print exception if given. """

    print('\n{}'.format(msg))
    if exc:
        print('Error:\n{}'.format(str(exc)))
    if retcode > -1:
        sys.exit(retcode)


def print_matches(matches, printlines=True, colorizer=None, names_only=False):
    """ print results, from list of single MatchInfo, or MatchCollection list.
        Arguments:
            matches     : A MatchCollection() (dir search)
                          or list of 1 MatchInfo() object (single-file search).

        Keyword Arguments:
            printlines  :  If True, print every line that matched.
                           (Default: True)
            colorizer   :  A ColorCodes() class to highlight with,
                           or None for no highlighting.
            names_only  :  Print file names only.
    """

    # Color theme for numbers (if colorizer was passed they are used)
    colorizer_args = {'style': 'bright',
                      'fore': 'green'}
    # Header/Footer for listing/finishing search details
    if names_only:
        header = '\nListing %s %s:'
        footer = '\nFound %s %s...'
    else:
        header = '\nListing %s %s in %s %s:\n'
        footer = '\nFound %s %s in %s %s...\n'

    # Helper functions
    # (used more than once, in different situations, helps to stay uniform.)
    def no_matches(cnt=None):
        """ Helper function, handles no matches found. """
        nomatchstr = '\nNo matches found.'
        if colorizer:
            nomatchstr = colorizer.word(nomatchstr, style='bright', fore='red')
        print(nomatchstr)
        if cnt is not None:
            print_searchedcount(cnt)

    def print_searchedcount(searchcount=None):
        """ Helper function, handles printing file count """
        if searchcount is None:
            searchcount = 0

        searchedplural = 'file' if searchcount == 1 else 'files'

        searchcount = str(searchcount)
        if colorizer:
            searchcount = colorizer.word(searchcount, **colorizer_args)
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
    if colorizer:
        filecount = colorizer.word(filecount, **colorizer_args)

    # Dir or Single File matches?
    if hasattr(matches, 'total_lines'):
        # match collection
        # (Actual MatchCollection() with helper attributes/functions)
        linecnt = matches.total_lines()
        linecount = str(linecnt)
        if colorizer:
            linecount = colorizer.word(linecount, **colorizer_args)
        plural_line = 'line' if linecnt == 1 else 'lines'
        plural_file = 'file' if filecnt == 1 else 'files'

        if printlines:
            print(header % (linecount, plural_line, filecount, plural_file))
            for match in matches.iterlines():
                print('    {}'.format(match))
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
        if colorizer:
            linecount = colorizer.word(linecount, **colorizer_args)
        plural_line = 'line' if linecnt == 1 else 'lines'
        plural_file = 'file'

        if printlines:
            print(header % (linecount, plural_line, filecount, plural_file))
            singlefilename = matches[0].filename
            if colorizer:
                singlefilename = colorizer.word(singlefilename,
                                                style='bright',
                                                fore='blue')
            print('{}: '.format(singlefilename))
        for lineinf in matches[0].iterlines():
            print('        {}'.format(str(lineinf)))
        searchedcount = 1

    # Print footer with match-count, file-count
    if names_only:
        print(footer % (filecount, plural_file))
    else:
        print(footer % (linecount, plural_line, filecount, plural_file))
    # Print number of files searched (with color if colorizer was passed)
    print_searchedcount(searchedcount)

    return 0


def printdebug(s):
    """ Just a debug print. Easily searched and replaced/deleted. """
    print(s)


# MAIN ENTRY POINT FUNCTION
def main(argd):
    """ main entry-point for searchpat, expects argument dict from docopt. """

    # Get ColorCodes() if applicable
    colors = None if argd['--nocolors'] else ColorCodes()

    # Get target file/dir/multiple files
    if not argd['<target>']:
        argd['<target>'] = [os.getcwd()]
    target = argd['<target>']

    # Get search term, compile it as a regex pattern
    searchterm = argd['<searchterm>']
    try:
        searchpat = re.compile(searchterm)
    except Exception as ex:
        print_fail('Invalid search term!: {}'.format(searchterm),
                   exc=ex,
                   retcode=1)

    # Get exclude pattern, compile it as a regex pattern.
    excludeterm = argd['--exclude']
    excludepat = None
    if excludeterm:
        try:
            excludepat = re.compile(excludeterm)
        except Exception as ex:
            print_fail('Invalid exclude pattern!: {}'.format(excludeterm),
                       exc=ex,
                       retcode=1)

    # Get maximum length, make sure it's a valid integer.
    maxlength = argd['--maxlength'] or 0
    try:
        maxlength = int(maxlength)
    except (TypeError, ValueError):
        print_fail('Invalid max length!: {}'.format(maxlength), retcode=1)
    else:
        if maxlength < 0:
            maxlength = 0

    # Colorize search type info, or use normal strings
    if len(target) > 1:
        # Multiple targets, may be files or directories
        # (could be shell-expanded *.whatever)
        if colors:
            targetlenstr = colors.word(str(len(target)),
                                       style='bright',
                                       fore='blue')
            targettypestr = colors.word('files/directories', fore='blue')
        else:
            targetlenstr = str(len(target))
            targettypestr = 'files/directories'
        targetstr = '{} {}'.format(targetlenstr, targettypestr)
        if colors:
            targetstr = colors.word(targetstr, fore='blue')
    else:
        if colors:
            targetstr = colors.word(target[0], fore='blue')
        else:
            targetstr = target[0]
    reversestr = '    *Reverse searching, looking for lines that don\'t match.'
    if colors:
        searchtermstr = colors.word(searchterm, fore='blue')
        reversestr = colors.word(reversestr, fore='red')
        excludetermstr = colors.word(excludeterm, fore='blue')
        maxlengthstr = colors.word(str(maxlength), fore='blue')
    else:
        searchtermstr = searchterm
        excludetermstr = excludeterm
        maxlengthstr = str(maxlength)

    searchstr = '    Searching: {}'.format(targetstr)
    patternstr = '      Pattern: {}'.format(searchtermstr)
    excludestr = '      Exclude: {}'.format(excludetermstr)
    maxlenstr = '   Max Length: {}'.format(maxlengthstr)
    # Print header
    print(searchstr)
    print(patternstr)
    if excludepat:
        print(excludestr)
    if maxlength > 0:
        print(maxlenstr)

    # Start time for search
    starttime = datetime.datetime.now()

    # Which search type is needed?
    if len(target) == 1 and (os.path.isfile(target[0]) or target[0] == '-'):
        # Single File Search / STDIN Search --------------------------------
        if argd['--reverse']:
            # Notify about reverse searching
            print(reversestr)

        if argd['--filenames']:
            # Only matching against the filename.
            matches = [get_filename_matches(target[0], searchpat,
                                            reverse=argd['--reverse'],
                                            debug=argd['--debug'],
                                            wholepath=argd['--wholepath'],
                                            excludepat=excludepat,
                                            colorizer=colors)]
        else:
            # Matching against a single file's content.
            if excludepat:
                msg = '--exclude will not work on a single file!'
                if colors:
                    msg = colors.word(msg, fore='red', style='bright')
                print(msg)

            matches = [get_file_matches(target[0], searchpat,
                                        reverse=argd['--reverse'],
                                        debug=argd['--debug'],
                                        colorizer=colors,
                                        maxlength=maxlength)]

        # Matches are printed after searching this single file
        printmatchlines = True

    elif len(target) == 1 and os.path.isdir(target[0]):
        # Directory Search --------------------------------------------------
        # Get filetypes to search.
        filetypes = parse_filetypes_arg(argd)
        # TODO:FORMAT THIS CODE BETTER, trimming to < 79 chars made it ugly!
        if filetypes:
            filetypes = sorted(filetypes)
        if colors:
            if filetypes:
                colortypes = [colors.word(s, fore='blue') for s in filetypes]
                filetypestr = ', '.join(colortypes)
            else:
                filetypestr = colors.word('All Files', fore='blue')
        else:
            filetypestr = ', '.join(filetypes) if filetypes else 'All Files'
        print('   File Types: {}'.format(filetypestr))
        # Reverse notify
        if argd['--reverse']:
            print(reversestr)

        # Do the search
        matches = get_dir_matches(target[0], searchpat,
                                  reverse=argd['--reverse'],
                                  filetypes=filetypes,
                                  debug=argd['--debug'],
                                  colorizer=colors,
                                  names_only=argd['--filenames'],
                                  wholepath=argd['--wholepath'],
                                  excludepat=excludepat,
                                  maxlength=maxlength)
        # Matches are printed as they are found, per file
        printmatchlines = False
    elif len(target) > 1:
        # Multiple Targets Search -------------------------------------------
        # Reverse notify
        if argd['--reverse']:
            print(reversestr)

        # Get file types to filter
        filetypes = parse_filetypes_arg(argd)

        # Do the search
        matches = get_multi_matches(target, searchpat,
                                    reverse=argd['--reverse'],
                                    filetypes=filetypes,
                                    debug=argd['--debug'],
                                    colorizer=colors,
                                    names_only=argd['--filenames'],
                                    wholepath=argd['--wholepath'],
                                    excludepat=excludepat,
                                    maxlength=maxlength)
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

    # Print header/footer and lines of applicable
    ret = print_matches(matches,
                        printlines=printmatchlines,
                        colorizer=colors,
                        names_only=argd['--filenames'])

    # Print run time
    runtime = '{:0.3f}'.format(runtime)
    if colors:
        runtime = colors.word(runtime, style='bright', fore='cyan')
    print('({} seconds)'.format(runtime))

    return ret


# START OF SCRIPT
if __name__ == '__main__':
    # Parse args, exit on usage failure.
    main_argd = docopt(usage_str, version=VERSIONSTR)
    # Go.
    main_ret = main(main_argd)
    sys.exit(main_ret)
