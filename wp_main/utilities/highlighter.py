# -*- coding: utf-8 -*-
''' Welborn Productions - Utilities - Highlighter
        Uses pygments to highlight source code and output it
        for welbornprod.com.

    -Christopher Welborn Mar 14, 2013
'''
import logging
import re
import lxml

from pygments import (
    highlight as pygments_highlight,
    lexers,
    formatters,
)
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
            codeh = pygments_highlight(code, self.lexer, self.formatter)
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


def copy_element(elem):
    """ Returns a copy of an HtmlElement. """
    return lxml.html.copy.deepcopy(elem)


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


def get_lexer_byname(sname, default='text'):
    """ retrieves a lexer by name, different than lexers.get_lexer_by_name()
        because it automatically enables certain options.
        this way all lexers for welbornprod will have the same options
        and can be set in one place.
    """

    try:
        lexer = lexers.get_lexer_by_name(sname, stripall=True,)
    except ClassNotFound:
        log.debug('Bad lexer name: {}'.format(sname))
        if default is None:
            raise
        return lexers.get_lexer_by_name(default, stripall=True)
    return lexer


def get_lexer_bynames(names, default=None):
    """ Given a list of possible lexer names, return the first one that
        works.
        If a `default` name is given, it's lexer is returned when no name
        matches.
        When `default` is None, and no name matches,
        pygments.util.ClassNotFound is raised.
    """
    errs = []
    for name in names:
        try:
            lexer = lexers.get_lexer_by_name(name)
            return lexer
        except ClassNotFound as ex:
            errs.append(ex)
    if default is not None:
        return lexers.get_lexer_by_name(default)
    # Just raise the last error.
    raise ClassNotFound(*errs[-1].args) from errs[-1]


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
    return lxml.html.tostring(
        wrap_elem(
            lxml.html.fromstring(text),
            tag=tag,
            newtag='div',
            processor=highlight_pre_elems,
        ),
        pretty_print=True,
        # <span></span><span class='blah'></span>
    ).decode()


def highlight_pre_elems(elem):
    """ Highlights pre tag content in an HtmlElement according to the classes
        set on the pre tags and transforms them into pre-like divs.
        This is a processor for wrap_elem().
        Returns the element on success, or None on error.
    """
    disallow_styles = {
        # Highlighting a template means the tag gets highlighted twice.
        'codewrap-template',
    }
    # Styles that won't be highlighted, but wrapped in a div.
    basic_styles = {
        'codewrap',
        'codewrap-noscript',
        'sampwrap',
        'sampwrap-noscript',
        'highlighted-inline'
    }

    # Go ahead and set the div's class, returning None means this element
    # isn't used anyway.
    elem.set('class', 'highlighted-inline')
    for preelem in elem.cssselect('pre'):
        preclass_str = preelem.get('class', '')
        classes = set(preclass_str.split(' '))
        if (not classes) or ('none' in classes):
            # No processing done, just set the class for the wrapping div.
            return elem
        elif classes.intersection(disallow_styles):
            # Cancel processing, contains a no-highlight-allowed class.
            return elem
        elif classes.intersection(basic_styles):
            # No processing done, class already set for pre tag.
            elem.set(
                'class',
                ' '.join((
                    elem.get('class', default='highlighted-inline'),
                    preclass_str,
                ))
            )
            return elem
        # Have a class set that is probably a language name for pygments.
        try:
            lexer = get_lexer_bynames(classes)
        except ClassNotFound:
            # No valid lexer. Just leave it.
            log.error('No lexer found with: {!r}'.format(
                preclass_str
            ))
            return elem

        # Highlight the pre tag's text using pygments.
        try:
            highlighted = pygments_highlight(
                preelem.text,
                lexer,
                DEFAULT_FORMATTER
            )
        except Exception as ex:
            log.error(
                '\n'.join((
                    'Failed to highlight pre tag: <p class={clsstr}>',
                    '    Source line: {sourceline}',
                    '    Error: {err}'
                )).format(
                    clsstr=preelem.get('class', default=''),
                    sourceline=preelem.sourceline,
                    err=ex,
                )
            )
            return elem

        # Highlight succeeded, replace the text with the highlight's html.
        preelem.text = ''
        preelem.append(lxml.html.fromstring(highlighted))

    return elem


def replace_elem(old, new):
    """ Replace an HtmlElement with a new one, either by calling
        old.getparent().replace(), or by adding the new one
        and removing the old one.
    """
    # Either add the new element after, or replace it in the parent.
    oldparent = old.getparent()
    if oldparent.tag == 'body':
        # This might mean that there was no parent, either way this works.
        old.addnext(new)
        old.remove()
    else:
        # Just replace the element using lxml's builtin method.
        oldparent.replace(old, new)


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

        highlighted = pygments_highlight(code, lexer, formatter)
        # log.debug('highlight: {}, {}'.format(langname, highlighted))
        return ''.join((
            '<div class="highlighted-embedded">',
            highlighted,
            '</div>'
        ))
    except Exception as ex:
        log.debug('try_highlight: Error highlighting.\n{}'.format(ex))
        return code


def wrap_elem(elem, tag='pre', newtag='div', processor=None):
    """ Wrap all pre tags in a `tag` with a class of `class_str`.
        Returns the new element, with replaced/wrapped tags.
        Arguments:
            elem       : An lxml.html.HtmlElement to search/replace in.
            tag        : Tags that should be wrapped.
                         Default: 'pre'
            newtag     : Tag for the wrapper.
                         Default: 'div'
            processor  : Function that processes each element.
                         It accepts each `newtag` element, after wrapping,
                         as the only argument.
                         It should return an HtmlElement on success, or None
                         to cancel processing and use an unprocessed element.
                         Default: None
    """
    wrapfmt = '<{tag}>\n{text}\n</{tag}>'.format
    for e in elem.cssselect(tag):
        if e.tag != tag:
            continue

        # Get the element's source code, for wrapping.
        ehtml = lxml.html.tostring(e).decode()
        # Wrap the old source in a `newtag`.
        newhtml = wrapfmt(tag=newtag, text=ehtml)
        # Create a new element from the wrapped source.
        newelem = lxml.html.fromstring(newhtml)
        # Process the element, if a processor was given.
        if processor and callable(processor):
            processedelem = processor(copy_element(newelem))
            if processedelem is not None:
                newelem = processedelem

        replace_elem(e, newelem)

    return elem
