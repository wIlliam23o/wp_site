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
    
    for sline in slines:
        strim = sline.replace(' ', '').replace('\t', '')
        # Inside a block, collect lines and wait for end.
        if inblock:
            if ("</" + tag_ + ">") in strim:
                
                inblock = False
                # highlight block
                soldblock = "\n".join(current_block)
                # must have both valid lexer/formatter
                if lexer is not None:
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
                current_block.append(sline)
        else:
            # Detect start
            if strim.startswith('<' + tag_ + 'class='):
                # get class name
                sclass = get_tag_class(sline, tag_)
                # check for name fixing
                # certain lexers share names with actual css selectors,
                # in a list of shortened blog entries the block may not be
                # highlighted
                # if the </pre> tag was cut off.
                # so pre class='c' is a valid statement even if highlighting
                # isn't done.
                # this causes the pre tag to be styled with the 'c' selector,
                # not as the 'c' language.
                # the workaround is to add a _ before known conflicting names.
                if sclass.startswith("_"):
                    sclass = sclass[1:]
                # empty class would break this.
                if sclass == "":
                    _log.error("encountered empty highlight class: " + sline)
                    return scode
                else:
                    if sclass.lower() == "none":
                        # no highlighting wanted here.
                        lexer = None
                        formatter = None
                        sclass = ""
                    else:
                        # try highlighting with this lexer name.
                        try:
                            lexer = get_lexer_byname(sclass)
                        except:
                            _log.error('highlight_inline: unable to create '
                                       'lexer/formatter with: '
                                       '{}'.format(sclass))
                            sclass = ''
                            lexer = None
                            formatter = None
                
                # don't attempt to highlight blocks where class is none.
                # its there for possible css styles/future development.
                # ...as long as the class isn't 'none', we are indeed inside
                #    a block that needs highlighting.
                inblock = (sclass.lower() != "none")

    return sfinished


def check_lexer_name(sname):
    """ checks against all lexer names to make sure this is a valid lexer name 
    """
    
    # retrieves list of tuples with valid lexer names
    lexer_list = [lexer_[1] for lexer_ in lexers.get_all_lexers()]
    # searches all tuples, returns True if its found.
    for names_tuple in lexer_list:
        if sname in names_tuple:
            return True
    return False


def get_all_lexer_names():
    """ retrieves list of all possible lexer names """
    
    # retrieves list of tuples with valid lexer names
    lexer_list = [lexer_[1] for lexer_ in lexers.get_all_lexers()]
    lexer_names = []
    for names_tuple in lexer_list:
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


def get_embedded_lexer(scode):
    """ retrieves lexer name from embedded highlight line.
        SHOULD BE REMOVED WHEN ALL POSTS/PROJECTS SWITCH TO HCODEPAT
    """
    tag_match = LEXERPAT.search(scode)
    if tag_match is None:
        return None
    else:
        tag_list = tag_match.group().split(' ')
        return tag_list[1 - tag_list.index('highlight-embedded')]


def get_embedded_code(scode, tag_="span"):
    """ retrieves code content from embedded highlight line.
        SHOULD BE REMOVED WHEN ALL POSTS/PROJECTS SWITCH TO HCODEPAT
    """
    patternstr = ('<' + tag_ +
                  r' class\=["\'](\w+[ ]highlight-embedded' +
                  r'|highlight-embedded[ ]\w+)["\']>(?P<content>.+)(?=</)')
    code_match = re.search(patternstr, scode)
    if code_match is None:
        return None
    else:
        if len(code_match.groups()) < 2:
            return None
        else:
            return code_match.groups()[1]


def get_embedded_line(scode, tag_="span"):
    """ retrieves the whole embedded line, tags and all.
        SHOULD BE REMOVED WHEN ALL POSTS/PROJECTS SWITCH TO HCODEPAT
    """
    patternstr = (r'<' + tag_ +
                  r' class\=["\'](\w+[ ]highlight-embedded' +
                  r'|highlight-embedded[ ]\w+)["\']>.+</' +
                  tag_ + '>')
    line_match = re.search(patternstr, scode)
    if line_match is None:
        return None
    else:
        return line_match.group()

    
def get_embedded_content(sline, tag_="span"):
    """ retrieves lexer and code from a single embedded highlight line.
        returns tuple of (lexer name, code to highlight) strings.
        returns None on error.
        SHOULD BE REMOVED WHEN ALL POSTS/PROJECTS SWITCH TO HCODEPAT
    """
    
    lexer_name = get_embedded_lexer(sline)
    code_content = get_embedded_code(sline, tag_)
    whole_line = get_embedded_line(sline, tag_)
    return (lexer_name, code_content, whole_line)
    

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
        newcode = try_highlight(code, langname)
        # Replace old text with new code.
        oldtext = ''.join(mgroups)
        scode = scode.replace(oldtext, newcode)

    if return_list:
        return scode.split('\n')
    else:
        return scode


def highlight_embedded(scode, tag_="span"):
    """ highlights embedded code, like:
        <p>
            To import the os module do
            <span class='highlight-embedded python'>import os</span> 
            at the top of your script.
        </p>
        
        tag must have the 'highlight-embedded' class, and the lexer name as
        the other class.
        if you intend to highlight two things on one line, you still must put
        the second on a seperate line. Your browser will join them together
        again. Using a single line for two highlights messes this up.

        SHOULD BE REMOVED WHEN ALL POSTS/PROJECTS SWITCH TO HCODEPAT
        (SOLVES THE SINGLE LINE PROBLEM, AND IS MUCH CLEANER TO WRITE)
    """
    
    if '\n' in scode:
        slines = scode.split('\n')
    else:
        # single line only.
        slines = [scode]
    formatter = formatters.html.HtmlFormatter(linenos=False,
                                              nowrap=True,
                                              style='default')
    newtagfmt = '<{tag} class=\'highlighted-embedded\'>{highlighted}</{tag}>'

    keep_lines = []
    for sline in slines:
        if 'highlight-embedded' in sline:
            lexer_name, content, whole_tag = get_embedded_content(sline)
            if ((lexer_name is None) or
               (content is None) or
               (whole_tag is None)):
                # error getting info from tag, use old line.
                keep_lines.append(sline)
            else:
                # highlight the embedded content.
                try:
                    lexer = lexers.get_lexer_by_name(lexer_name)
                    highlighted = pygments.highlight(content,
                                                     lexer,
                                                     formatter)
                    snewtag = newtagfmt.format(tag=tag_,
                                               highlighted=highlighted)
                    # replace old content with new highlighted content.
                    snewline = sline.replace(whole_tag, snewtag)
                    keep_lines.append(snewline)
                except:
                    _log.debug('highlight_embedded: '
                               'invalid lexer name in: {}'.format(whole_tag))
                    keep_lines.append(sline)
        else:
            # no embedding needed
            keep_lines.append(sline)
            
    return '\n'.join(keep_lines)
