# -*- coding: utf-8 -*-
''' Welborn Productions - Utilities - Highlighter
        Uses pygments to highlight source code and output it
        for welbornprod.com.

    -Christopher Welborn Mar 14, 2013
'''
import logging
import re
import pygments
from pygments import formatters
from pygments import lexers
from pygments.util import ClassNotFound

from django.utils.safestring import mark_safe
from django.utils.html import escape


log = logging.getLogger('wp.utilities.highlighter')
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
STYLECODES = {
    'b': '<span class=\'B\'>{}</span>',
    'i': '<span class=\'I\'>{}</span>',
    # This 'l' (link) code requires 2 arguments separated by |.
    # The first arg is the text, the second is the link target.
    # Links are opened in a new (blank) window.
    'l': '<a href=\'{1}\' target=\'_blank\'>{0}</a>',
    'u': '<span style=\'text-decoration: underline;\'>{}</span>',
    'code': '<div class=\'codewrap\'>{}</div>',
}

# Aliases for pygments lexer names. These are switched to the long name
# before highlighting.
STYLEALIASES = {
    'py': 'python',
}
STYLENAMES = list(STYLECODES.keys())

# Preload the default formatter.
try:
    DEFAULT_FORMATTER = formatters.html.HtmlFormatter(
        linenos=False,
        nowrap=True,
        style='default')
except AttributeError:
    # Pygments 2.0.2+
    DEFAULT_FORMATTER = formatters.get_formatter_by_name('html')
    DEFAULT_FORMATTER.linenos = False
    DEFAULT_FORMATTER.nowrap = True
    DEFAULT_FORMATTER.style = 'default'


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
            log.error('WpHighlighter.highlight() error:\n{}'.format(ex))
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
        log.debug('Bad lexer name: {}'.format(sname))
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


def get_tag_classes(text, tag='pre'):
    """ Grabs class names from a pre tag for highlight_inline() """
    if '<{} class='.format(tag) not in text:
        return []

    classpat = re.compile(
        r'class=[{quotes}]{{1}}([\d\w\-_ ]+)'.format(
            quotes='\'"',
        ),
        flags=re.IGNORECASE
    )
    tagstrs = classpat.findall(text)
    if not tagstrs:
        return []
    if len(tagstrs) > 1:
        log.error('Grabbed too many class names from: {}'.format(text))
    return tagstrs[0].strip().split()


def highlight_codes(text):
    """ Highlights embedded wp highlight codes.
        like: [lang]lang code here[/lang]
    """
    if isinstance(text, (list, tuple)):
        return_list = True
        text = '\n'.join(text)
    else:
        return_list = False

    formatter = DEFAULT_FORMATTER

    # Search lines for original codes (HCODEPAT)..
    matches = HCODEPAT.findall(text)
    # ...alternate method [code]...[?code] uses ? instead of / to get around
    #    code with / in it. (uses HCODEPAT2 to find them)
    newmatches = HCODEPAT2.findall(text)
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
        text = text.replace(oldtext, newcode)

    if return_list:
        return text.split('\n')
    else:
        return text


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
            log.error('Error highlighting file: {}\n'.format(static_path) +
                      '{}'.format(str(ex)))
    else:
        # No lexer, so no highlighting, still need to format it a bit.
        file_content = escape(file_content).replace('\n', '<br>')

    return mark_safe(file_content)


def highlight_inline(text, tag='pre'):
    """ Highlights inline code for html strings.
        If code is wrapped with <pre class='python'> this function
        will find it and replace it with highlighted python code.
        The class can be any valid pygments lexer name.
        If no tag is found the original string is returned.
    """

    if '<{} class='.format(tag) not in text:
        # No tag at all, no highlighting.
        return text

    # Whether we are currently processing a tag's contents.
    inblock = False
    # Blocks of text inside of the tag, tags not included.
    current_block = []
    # Lexer decided by class name on the tags.
    lexer = None
    # Styles that trigger a cancel,
    disallow_styles = {
        # Highlighting a template means the tag gets highlighted twice.
        'codewrap-template',
    }
    # Styles that won't be highlighted, but wrapped in a div.
    basic_styles = {
        'none',
        'codewrap',
        'codewrap-noscript',
        'sampwrap',
        'sampwrap-noscript',
        'highlighted-inline'
    }
    # For detecting starts/stops.
    opentag = '<{}class='.format(tag)
    closetag = '</{}>'.format(tag)
    outlines = []

    for line in text.split('\n'):
        trimmed = line.replace(' ', '').replace('\t', '')
        # Inside a block, collect lines and wait for end.
        if inblock:
            if closetag not in trimmed:
                # Add this line to the block that will be wrapped/highlighted
                current_block.append(line)
                continue
            # End of block.
            inblock = False
            # Decide how to wrap/highlight it..
            # class = 'none or 'codewrap', etc. was used, just wrap it.
            append_end_div = False
            if lexer in basic_styles:
                # No highlighting, just wrap it.
                # if pre class='codewrap' was used, the 'codewrap' style
                # will still be applied to the pre tag.
                # if pre class='none' was used, the 'highlighted-inline'
                # class will be applied.
                if lexer == 'none':
                    outlines.append('<div class=\'highlighted-inline\'>')
                    outlines.extend(current_block)
                    append_end_div = True
                else:
                    # plain div, the parent tag applied some style.
                    outlines.append('<div class="pre-{}-plain">'.format(
                        lexer
                    ))
                    outlines.extend(current_block)
                    append_end_div = True

            # must have valid lexer for highlighting
            elif lexer is not None:
                # Highlight the old block of text.
                outlines.append(highlight_inline_block(
                    '\n'.join(current_block),
                    lexer,
                    DEFAULT_FORMATTER
                ))
            # Add closing pre tag.
            outlines.append(line)
            if append_end_div:
                outlines.append('</div>')
            # clear block
            current_block = []
            continue

        # Detect start
        if trimmed.startswith(opentag):
            outlines.append(line)
            # get class name
            classes = get_tag_classes(line, tag=tag)
            if not classes:
                # Error while parsing class name probably extra info in
                # the tag. like: <pre class='test' style='breaker'>
                # Code will not be highlighted.
                log.error(
                    'Unable to parse class attribute from {}'.format(
                        line
                    )
                )
                continue

            # check for name fixing
            # names can start with '_' like '_c' in case they share
            # a name with other css classes.
            classes = [s.lstrip('_') for s in classes]
            for clsname in classes:
                clsnamelower = clsname.lower()
                if clsnamelower in disallow_styles:
                    # This class means the file should not be highlighted.
                    return text
                if clsnamelower in basic_styles:
                    # no highlighting wanted here.
                    # but we will wrap it in a <div class='highlighted...'
                    lexer = clsname
                    inblock = True
                elif clsname:
                    # try highlighting with this lexer name.
                    try:
                        lexer = get_lexer_byname(clsname)
                    except:
                        log.error(
                            ' '.join((
                                'highlight_inline: unable to create ',
                                'lexer/formatter with: {}'
                            )).format(clsname)
                        )
                        lexer = None
                    # Set the flag to start collecting lines.
                    inblock = True
                else:
                    # No class
                    log.error(
                        'encountered empty highlight class: {}'.format(line)
                    )
                    return text

        else:
            # Non-related code line.
            outlines.append(line)
    # Finished with all lines.
    return '\n'.join(outlines)


def highlight_inline_block(text, lexer, formatter):
    """ Highlight a block of text and wrap in a .highlighted-inline div.
        Helper method for highlight_inline().
        Returns the highlighted text on success.
        On errors, it logs the error and returns the original text.
    """
    if formatter is None:
        formatter = DEFAULT_FORMATTER
    if lexer is None:
        log.error('highlight_inline_block: No lexer given, using \'text\'.')
        lexer = lexers.get_lexer_by_name('text')

    try:
        highlighted = pygments.highlight(text, lexer, formatter)
    except Exception as ex:
        log.error('highlight_inline(): Error:\n{}'.format(ex))
        highlighted = text

    return '\n'.join((
        '\n<div class=\'highlighted-inline\'>',
        highlighted,
        '</div>\n',
    ))


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
            log.debug(
                'try_highlight: No lexer found for  {}'.format(langname)
            )
            return code

        highlighted = pygments.highlight(code, lexer, formatter)
        # log.debug('highlight: {}, {}'.format(langname, highlighted))
        return ''.join((
            '<div class="highlighted-embedded">',
            highlighted,
            '</div>'
        ))
    except Exception as ex:
        log.debug('try_highlight: Error highlighting.\n{}'.format(ex))
        return code
