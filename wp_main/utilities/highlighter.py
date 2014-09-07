# -*- coding: utf-8 -*-
''' Welborn Productions - Utilities - Highlighter
        Uses pygments to highlight source code and output it
        for welbornprod.com.

    -Christopher Welborn Mar 14, 2013
'''

from django.utils.safestring import mark_safe
from django.utils.html import escape

import pygments
from pygments import formatters
from pygments import lexers
from pygments.util import ClassNotFound

from wp_main.utilities.wp_logging import logger

# for embedded highlighting
import re

_log = logger('utilities.highlighter').log
# Regex pattern for wp highlight codes.
# [language]insert code here[/language]
# Use .findall() with it.
HCODEPAT = re.compile(r'(\[[\w\d]+\])([^\[/]+)(\[/[\w\d+]+\])')
# This is an alternate method for highlight codes.
# It uses [language]text[?language] to recognize the codes.
# Use it for code that contains the '/' character.
HCODEPAT2 = re.compile(r'(\[[\w\d]+\])([^\[\?]+)(\[\?[\w\d+]+\])')

# List of valid lexer names.
LEXERNAMES = [lexer_[1] for lexer_ in lexers.get_all_lexers()]

# Basic style codes
STYLECODES = {'b': '<span class=\'B\'>{}</span>',
              'i': '<span class=\'I\'>{}</span>',
              # This 'l' (link) code requires 2 arguments separated by |.
              # The first arg is the text, the second is the link target.
              # Links are opened in a new (blank) window.
              'l': '<a href=\'{1}\' target=\'_blank\'>{0}</a>',
              'u': '<span style=\'text-decoration: underline;\'>{}</span>',
              'code': '<div class=\'codewrap\'>{}</div>',
              # These are used to build cmd-help lists.
              'cmdoption': '<div class=\'cmdoption\'>{}</div>',
              'cmdvalue': '<div class=\'cmdvalue\'>{}</div>',
              }

# Aliases for pygments lexer names. These are switched to the long name
# before highlighting.
STYLEALIASES = {'py': 'python',
                'cmdopt': 'cmdoption',
                'cmdval': 'cmdvalue',
                'copt': 'cmdoption',
                'cval': 'cmdvalue',
                }
STYLENAMES = list(STYLECODES.keys())

# Preload the default formatter.
DEFAULT_FORMATTER = formatters.html.HtmlFormatter(
    linenos=False,
    nowrap=True,
    style='default')


class WpHighlighter(object):

    """ Class for highlighting code and returning html markup. """

    def __init__(
        self,
        lexer_name=None, style_name=None, line_nums=False, code=None,
        classes=None):
            self.code = code or ''
            self.classes = classes or []
            self.lexer_name = lexer_name if lexer_name else 'python'
            self.lexer = get_lexer_byname(self.lexer_name)
            self.style_name = style_name if style_name else 'default'
            self.line_nums = line_nums
            self.formatter = formatters.html.HtmlFormatter(
                linenos=self.line_nums,
                style=self.style_name)

    def set_lexer(self, lexer_name):
        """ another way to set the lexer """
        trylexer = get_lexer_byname(lexer_name)
        self.lexer = trylexer
        self.lexer_name = lexer_name

    def highlight(self, code=None, classes=None):
        """ returns highlighted code in html format
            styles are not included, you must have a
            css file on hand and reference it.
        """
        if not code:
            code = self.code
        if not classes:
            classes = self.classes
        # Default class for all highlighted code (for the div wrapper)
        classlist = ['highlighted']
        if classes:
            # User defined classes, may override the default class.
            classlist.extend(classes)

        classtxt = ' '.join(classlist)

        try:
            codeh = pygments.highlight(code, self.lexer, self.formatter)
            highlighted = '\n'.join([
                '<div class=\'{}\'>'.format(classtxt),
                codeh,
                '</div>\n'])

        except Exception as ex:
            _log.error('WpHighlighter.highlight() error:\n{}'.format(ex))
            highlighted = ''
        return highlighted

    def get_styledefs(self):
        """ return css style definitions (for debugging really) """

        return self.formatter.get_style_defs()


def check_lexer_name(sname):
    """ checks against all lexer names to make sure this is a valid lexer name
    """

    # searches all tuples, returns True if its found.
    for names_tuple in LEXERNAMES:
        if sname in names_tuple:
            return True
    return False


def get_all_lexer_names():
    """ retrieves list of all possible lexer names """

    # retrieves list of tuples with valid lexer names
    lexer_names = []
    for names_tuple in LEXERNAMES:
        for name_ in names_tuple:
            lexer_names.append(name_)
    return lexer_names


def get_hcode_code(mgroups):
    """ Retrieve code to be highlighted from match groups. """
    if mgroups:
        code = mgroups[1].strip()
        return code
    return None


def get_hcode_language(mgroups):
    """ Retrieve desired language from match groups.
        Gets language name from the first group matched: '[language]'
    """

    if mgroups:
        lang = mgroups[0].strip('[').strip(']')
        return lang.lower().strip()
    return None


def get_lexer_byname(sname):
    """ retrieves a lexer by name, different than lexers.get_lexer_by_name()
        because it automatically enables certain options.
        this way all lexers for welbornprod will have the same options
        and can be set in one place.
    """

    try:
        lexer = lexers.get_lexer_by_name(sname, stripall=True,)
    except ClassNotFound:
        _log.debug('Bad lexer name: {}'.format(sname))
        return lexers.get_lexer_by_name('text', stripall=True)
    return lexer


def get_lexer_fromfile(sfilename):
    """ return a lexer based on filename. """

    try:
        lexer_ = lexers.get_lexer_for_filename(sfilename)
    except:
        # no lexer found.
        lexer_ = None
    return lexer_


def get_lexer_name_fromcontent(content):
    """ determine lexer from shebang line if any is present. """

    if isinstance(content, (list, tuple)):
        # readlines() was passed.
        firstline = content[0]
    else:
        if '\n' in content:
            # not calling split() here.
            firstline = content[:content.index('\n')]
        else:
            # Can't determine usable first line.
            return ''
    # Got usable first line, look for shebang.
    if firstline.startswith('#!'):
        # get interpreter from shebang line.
        shebanglang = firstline.split('/')[-1]
        # check for env use ('env python')
        if ' ' in shebanglang:
            # interpreter name should be last thing
            shebanglang = shebanglang.split()[-1]
        return shebanglang.strip()
    # didn't work, no language found.
    return ''


def get_lexer_name_fromfile(sfilename):
    """ determine which lexer to use by file extension """

    try:
        lexer_ = lexers.get_lexer_for_filename(sfilename)
        lexer_name = lexer_.aliases[0]
    except:
        # no lexer found
        lexer_name = ''
    return lexer_name


def get_tag_class(text, tag='pre'):
    """ Grabs class name from a pre tag for highlight_inline() """
    if ('<{} class='.format(tag) in text) and ('>' in text):
        sclass = text.split('=')[1]
        if '>' in sclass:
            sclass = sclass[:sclass.index('>')]
            if "'" in sclass:
                sclass = sclass.replace("'", '')
            elif '"' in sclass:
                sclass = sclass.replace('"', '')
        else:
            # A style or something was added to the <pre> tag, it breaks this.
            return None
    else:
        sclass = ''
    return sclass


def highlight_codes(scode):
    """ Highlights embedded wp highlight codes.
        like: [lang]lang code here[/lang]
    """
    if isinstance(scode, (list, tuple)):
        return_list = True
        scode = '\n'.join(scode)
    else:
        return_list = False

    formatter = DEFAULT_FORMATTER

    # Search lines for original codes (HCODEPAT)..
    matches = HCODEPAT.findall(scode)
    # ...alternate method [code]...[?code] uses ? instead of / to get around
    #    code with / in it. (uses HCODEPAT2 to find them)
    newmatches = HCODEPAT2.findall(scode)
    if newmatches:
        # New-style matches were found, add them to the 'matches' list.
        matches.extend(newmatches)

    aliasnames = STYLEALIASES.keys()
    for mgroups in matches:
        langname = get_hcode_language(mgroups)
        code = get_hcode_code(mgroups)
        # Aliases are checked first, and converted to the long name.
        if langname in aliasnames:
            langname = STYLEALIASES[langname]
        # Check if this is a style-code or lang-name and format accordingly.
        if langname in STYLENAMES:
            # catch basic style codes such as [b] and [i][/i].
            if '|' in code:
                # This style requires two arguments.
                styleargs = [s.strip() for s in code.split('|')]
                newcode = STYLECODES[langname].format(*styleargs)
            else:
                # Basic style code, only needs 1 format argument.
                newcode = STYLECODES[langname].format(code)
        else:
            # Do highlighting based on language name [python] or [bash].
            # (any valid pygments lexer)
            # Try highlighting the code with this language/lexer name.
            newcode = try_highlight(code, langname, formatter=formatter)
        # Replace old text with new code.
        oldtext = ''.join(mgroups)
        scode = scode.replace(oldtext, newcode)

    if return_list:
        return scode.split('\n')
    else:
        return scode


def highlight_file(static_path, file_content):
    """ Highlight a file's content. The lexer is chosen by the file path.
        Arguments:
            static_path  : File path to determine lexer from.
            file_content : String to highlight. (a file's content)
    """
    # Get pygments lexer
    lexername = get_lexer_name_fromfile(static_path)
    if not lexername:
        # Try getting lexer from first line in file.
        lexername = get_lexer_name_fromcontent(file_content)

    # Highlight the file (if needed)
    if lexername:
        try:
            highlighter = WpHighlighter(lexername, 'default', line_nums=False)
            highlighter.code = file_content
            file_content = highlighter.highlight()
        except Exception as ex:
            _log.error('Error highlighting file: {}\n'.format(static_path) +
                       '{}'.format(str(ex)))
    else:
        # No lexer, so no highlighting, still need to format it a bit.
        file_content = escape(file_content).replace('\n', '<br>')

    return mark_safe(file_content)


def highlight_inline(scode, tag='pre'):
    """ highlights inline code for html strings.
        if code is wrapped with <pre class='python'> this function
        will find it and replace it with highlighted python code.
        the class can be any valid pygments lexer name.
        if no tag is found the original string is returned.
    """

    if not '<{} class='.format(tag) in scode:
        #_log.debug('highlight_inline: Will not be highlighted.')
        return scode

    slines = scode.split('\n')
    sclass = ''
    inblock = False
    current_block = []
    lexer = None
    formatter = DEFAULT_FORMATTER
    sfinished = scode
    # Styles that won't be highlighted, but wrapped in a div
    basic_styles = ('none', 'codewrap', 'sampwrap', 'highlighted-inline')
    # For detecting starts/stops.
    opentag = '<{}class='.format(tag)
    closetag = '</{}>'.format(tag)
    for sline in slines:
        strim = sline.replace(' ', '').replace('\t', '')
        # Inside a block, collect lines and wait for end.
        if inblock:
            if closetag in strim:
                # End of block.
                inblock = False
                # highlight block
                soldblock = '\n'.join(current_block)
                # class = 'none or 'codewrap', etc. was used, just wrap it.
                if lexer in basic_styles:
                    # No highlighting, just wrap it.
                    # if pre class='codewrap' was used, the 'codewrap' style
                    # will still be applied to the pre tag.
                    # if pre class='none' was used, the 'highlighted-inline'
                    # class will be applied.
                    if lexer == 'none':
                        newblock = ''.join([
                            '<div class=\'highlighted-inline\'>',
                            '{}'.format(soldblock),
                            '</div>'])
                    else:
                        # plain div, the parent tag applied some style.
                        newblock = '<div>\n{}\n</div>'.format(soldblock)
                    # newlines for human-readable source.
                    newblock = '\n{}\n'.format(newblock)
                    sfinished = sfinished.replace(soldblock, newblock)
                # must have valid lexer for highlighting
                elif lexer is not None:
                    # Highlight the old block of text.
                    try:
                        highlighted = pygments.highlight(soldblock,
                                                         lexer,
                                                         formatter)
                    except Exception as ex:
                        _log.error('highlight_inline(): Error:\n{}'.format(ex))
                        highlighted = soldblock

                    newblock = [
                        '\n<div class=\'highlighted-inline\'>',
                        highlighted,
                        '</div>\n',
                    ]
                    sfinished = sfinished.replace(
                        soldblock,
                        '\n'.join(newblock))
                # clear block
                current_block = []
            else:
                # Add this line to the block that will be wrapped/highlighted
                current_block.append(sline)
        else:
            # Detect start
            if strim.startswith(opentag):
                # get class name
                sclass = get_tag_class(sline, tag=tag)
                if sclass is None:
                    # Error while parsing class name probably extra info in
                    # the tag. like: <pre class='test' style='breaker'>
                    # Code will not be highlighted.
                    _log.error('Unable to parse class attribute from '
                               '{}'.format(strim))
                else:
                    # check for name fixing
                    # names can start with '_' like '_c' in case they share
                    # a name with other css classes.
                    if sclass.startswith('_'):
                        sclass = sclass[1:]
                    if sclass.lower() in basic_styles:
                        # no highlighting wanted here.
                        # but we will wrap it in a <div class='highlighted...'
                        lexer = sclass
                        sclass = ''
                        inblock = True
                    elif sclass:
                        # try highlighting with this lexer name.
                        try:
                            lexer = get_lexer_byname(sclass)
                        except:
                            _log.error('highlight_inline: unable to create '
                                       'lexer/formatter with: '
                                       '{}'.format(sclass))
                            sclass = ''
                            lexer = None
                        # Set the flag to start collecting lines.
                        inblock = True
                    else:
                        # No class
                        _log.error((
                            'encountered empty highlight class:  {}'
                        ).format(sline))
                        return scode

    # Finished with all lines.
    return sfinished


def try_highlight(code, langname, formatter=None):
    """ Try highlighting a line of text.
        Return the highlighted code on success,
        return unhighlighted code on failure.
    """
    if formatter is None:
        # Formatter was not preloaded by the user,
        # Use the default preloaded html formatter.
        formatter = DEFAULT_FORMATTER

    try:
        lexer = lexers.get_lexer_by_name(langname)
        if not lexer:
            _log.debug('try_highlight: No lexer found for '
                       '{}'.format(langname))
            return code

        highlighted = pygments.highlight(code, lexer, formatter)
        #_log.debug('highlight: {}, {}'.format(langname, highlighted))
        return ''.join([
            '<div class="highlighted-embedded">',
            highlighted,
            '</div>'])
    except Exception as ex:
        _log.debug('try_highlight: Error highlighting.\n{}'.format(ex))
        return code
