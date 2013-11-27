# -*- coding: utf-8 -*-

'''
      project: welbornprod.viewer.highlighter
     @summary: uses pygments to highlight source code and output it 
               for welbornproductions.net
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 14, 2013
'''
import pygments
from pygments import formatters
from pygments import lexers
from wp_main.utilities.wp_logging import logger

# for embedded highlighting
import re

_log = logger('utilities.highlighter').log
# Regex pattern for wp highlight codes.
# [language]insert code here[/language]
# Use .findall() with it.
HCODEPAT = re.compile(r'(\[[\w\d]+\])([^\[/]+)(\[/[\w\d+]+\])')
# Regex pattern for grabbing lexer names from:
# <span class='highlight-embedded LEXERNAME'>
# SHOULD BE REMOVED AFTER ALL POSTS/PROJECTS SWITCH TO HCODEPAT STYLE.
LEXERPAT = re.compile(r'\w+[ ]highlight-embedded|highlight-embedded[ ]\w+')

# List of valid lexer names.
LEXERNAMES = [lexer_[1] for lexer_ in lexers.get_all_lexers()]

# Basic style codes
STYLECODES = {'b': '<span class=\'B\'>{}</span>',
              'i': '<span class=\'I\'>{}</span>',
              }
STYLENAMES = list(STYLECODES.keys())


class wp_highlighter(object):

    """ Class for highlighting code and returning html markup. """
    
    def __init__(self, lexer_name=None, style_name=None, line_nums=True):
        self.code = ""
        self.lexer_name = lexer_name if lexer_name else 'python'
        self.lexer = get_lexer_byname(self.lexer_name)
        self.style_name = style_name if style_name else 'default'
        self.line_nums = line_nums
        self.formatter = formatters.html.HtmlFormatter(linenos=self.line_nums,
                                                       style=self.style_name)

    def set_lexer(self, lexer_name):
        """ another way to set the lexer """
        trylexer = get_lexer_byname(lexer_name)
        if trylexer:
            self.lexer = trylexer
            self.lexer_name = lexer_name

    def highlight(self):
        """ returns highlighted code in html format
            styles are not included, you must have a
            css file on hand and reference it.
        """
        
        try:
            code = pygments.highlight(self.code, self.lexer, self.formatter)
            highlighted = '\n'.join(['<div class=\'highlighted\'>\n',
                                     code,
                                     '\n</div>',
                                     ])
        except Exception as ex:
            _log.error('wp_highlighter.highlight() error:\n{}'.format(ex))
            highlighted = ''
        return highlighted
    
    def get_styledefs(self):
        """ return css style definitions (for debugging really) """
        
        return self.formatter.get_style_defs()
    
    
def get_tag_class(stext, tag_="pre"):
    """ grabs class name from a pre tag for auto-highlighting """
    if "<" + tag_ + " class=" in stext and ">" in stext:
        sclass = stext.split('=')[1]
        sclass = sclass[:sclass.index('>')]
        if "'" in sclass:
            sclass = sclass.replace("'", '')
        elif '"' in sclass:
            sclass = sclass.replace('"', '')
    else:
        sclass = ""
    return sclass


def highlight_inline(scode, tag_="pre"):
    """ highlights inline code for html strings.
        if code is wrapped with <pre class='python'> this function
        will find it and replace it with highlighted python code.
        the class can be any valid pygments lexer name.
        if no tag is found the original string is returned.
    """
    
    if not "<" + tag_ + " class=" in scode:
        _log.debug('highlight_inline: no tag or class found, '
                   'will not be highlighted.')
        return scode
    slines = scode.split('\n')
    sclass = ""
    inblock = False
    current_block = []
    lexer = None
    formatter = formatters.html.HtmlFormatter(linenos=False, style="default")
    sfinished = scode
    # Styles that won't be highlighted, but wrapped in their own class,
    # none will get at least a 'highlighted-inline' class.
    basic_styles = ('none', 'codewrap', 'sampwrap', 'highlighted-inline')
    for sline in slines:
        strim = sline.replace(' ', '').replace('\t', '')
        # Inside a block, collect lines and wait for end.
        if inblock:
            if ("</" + tag_ + ">") in strim:
                # End of block.
                inblock = False
                # highlight block
                soldblock = "\n".join(current_block)
                # class = 'none or 'codewrap', etc. was used, just wrap it.
                if lexer in basic_styles:
                    # No highlighting, just wrap it.
                    if lexer == 'none':
                        newclass = 'highlighted-inline'
                    else:
                        newclass = lexer
                    newblock = ['\n<div class=\'{}\'>'.format(newclass),
                                soldblock,
                                '</div>\n',
                                ]
                    sfinished = sfinished.replace(soldblock,
                                                  '\n'.join(newblock))
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

                    newblock = ['\n<div class=\'highlighted-inline\'>',
                                highlighted,
                                '</div>\n',
                                ]
                    sfinished = sfinished.replace(soldblock,
                                                  '\n'.join(newblock))
                # clear block
                current_block = []
            else:
                # Add this line to the block that will be wrapped/highlighted
                current_block.append(sline)
        else:
            # Detect start
            if strim.startswith('<' + tag_ + 'class='):
                # get class name
                sclass = get_tag_class(sline, tag_)
                # check for name fixing
                # names can start with '_' like '_c' in case they share
                # a name with other css classes.
                if sclass.startswith("_"):
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
                    _log.error("encountered empty highlight class: " + sline)
                    return scode
                    inblock = False

    # Finished with all lines.
    return sfinished


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


def get_lexer_byname(sname):
    """ retrieves a lexer by name, different than lexers.get_lexer_by_name()
        because it automatically enables certain options.
        this way all lexers for welbornprod will have the same options
        and can be set in one place.
    """
    
    return lexers.get_lexer_by_name(sname, stripall=True,)


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


def get_lexer_fromfile(sfilename):
    """ return a lexer based on filename. """

    try:
        lexer_ = lexers.get_lexer_for_filename(sfilename)
    except:
        # no lexer found.
        lexer_ = None
    return lexer_
    

def highlight_codes(scode):
    """ Highlights embedded wp highlight codes.
        like: [lang]lang code here[/lang]
    """

    if isinstance(scode, (list, tuple)):
        return_list = True
        scode = '\n'.join(scode)
    else:
        return_list = False

    def get_language(mgroups):
        """ Retrieve desired language from match groups. """

        if mgroups:
            lang = mgroups[0].strip('[').strip(']')
            return lang.lower().strip()
        return None

    def get_code(mgroups):
        """ Retrieve code to be highlighted from match groups. """
        if mgroups:
            code = mgroups[1].strip()
            return code
        return None

    formatter = formatters.html.HtmlFormatter(linenos=False,
                                              nowrap=True,
                                              style='default')

    def try_highlight(code, langname):
        """ Try highlighting a line of text.
            Return the highlighted code on success,
            return unhighlighted code on failure.
        """
        try:
            lexer = lexers.get_lexer_by_name(langname)
            if not lexer:
                _log.debug('highlight_codes: No lexer found for '
                           '{}'.format(langname))
                return code
            
            highlighted = pygments.highlight(code, lexer, formatter)
            #_log.debug('highlight: {}, {}'.format(langname, highlighted))
            return ''.join(['<div class="highlighted-embedded">',
                            highlighted,
                            '</div>'])
        except Exception as ex:
            _log.debug('highlight_codes: Error highlighting.\n{}'.format(ex))
            return code

    # Search lines..
    matches = HCODEPAT.findall(scode)
    for mgroups in matches:
        langname = get_language(mgroups)
        code = get_code(mgroups)
        if langname in STYLENAMES:
            # catch basic style codes.
            newcode = STYLECODES[langname].format(code)
        else:
            # Do highlighting.
            newcode = try_highlight(code, langname)
        # Replace old text with new code.
        oldtext = ''.join(mgroups)
        scode = scode.replace(oldtext, newcode)

    if return_list:
        return scode.split('\n')
    else:
        return scode


def get_style_code(stylename):
    """ Retrieves the html needed to format text based on styles like:
        [b]bold text[/b] [i]italic text[/i].
    """
