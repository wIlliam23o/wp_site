#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welbornprod.viewer.highlighter
     @summary: uses pygments to highlight source code and output it for welbornproductions.net
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 14, 2013
'''
import pygments
from pygments import formatters
from pygments import lexers
import logging
# for embedded highlighting
import re

hl_log = logging.getLogger('welbornprod.viewer.highlighter')

class wp_highlighter(object):
    """ Class for highlighting code and returning html markup. """
    
    def __init__(self, lexer_name_ = "python", style_name_ = "default", line_nums_ = True):
        self.code = ""
        self.lexer_name = lexer_name_
        self.lexer = lexers.get_lexer_by_name(self.lexer_name)
        self.style_name = style_name_
        self.line_nums = line_nums_
        self.formatter = formatters.html.HtmlFormatter(linenos=self.line_nums, style=self.style_name)
        
    def set_code(self, scode):
        """ another way to set what code is highlighted. """
        self.code = scode
    
    def set_lexer(self, lexer_name_):
        """ another way to set the lexer """
        self.lexer = lexers.get_lexer_by_name(lexer_name_)
        self.lexer_name = lexer_name_
            
    def highlight(self):
        """ returns highlighted code in html format
            styles are not included, you must have a
            css file on hand and reference it.
        """
        
        try:
            highlighted = "<div class='highlighted'>" + pygments.highlight(self.code.strip().strip('\t'), self.lexer, self.formatter) + "</div>"
        except:
            highlighted = ""
        return highlighted
    
    
    def get_styledefs(self):
        """ return css style definitions (for debugging really) """
        
        return self.formatter.get_style_defs()
    
    
def get_tag_class(stext, tag_ = "pre"):
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


def highlight_inline(scode, tag_ = "pre"):
    """ highlights inline code for html strings.
        if code is wrapped with <pre class='python'> this function
        will find it and replace it with highlighted python code.
        the class can be any valid pygments lexer name.
        if no tag is found the original string is returned.
    """
    
    if not "<" + tag_ + " class=" in scode:
        return scode

    slines = scode.split('\n')
    sclass = ""
    inblock = False
    current_block = []
    lexer_ = None
    formatter_ = None
    sfinished = scode
    
    for sline in slines:
        strim = sline.replace(' ', '').replace('\t', '')
        # Already in block?
        if inblock:
            if strim.endswith("</" + tag_ + ">"):
                inblock = False
                # highlight block
                soldblock = "\n".join(current_block)
                if ((formatter_ is None) or
                    (lexer_ is None)):
                    hl_log.error("highlight_inline: tryed to highlight code without lexer and formatter! (=None)")
                else:
                   
                    snewblock = "\n<div class='highlighted-inline'>\n" + \
                                pygments.highlight(soldblock, lexer_, formatter_) + \
                                "\n</div>\n"
                                
                    sfinished = sfinished.replace(soldblock, snewblock)
                # clear block
                current_block = []
            else:
                current_block.append(sline)
        else:    
            # Detect start
            if strim.startswith('<' + tag_ + 'class='):
                # get class name
                sclass = get_tag_class(sline, tag_)
                if sclass == "":
                    hl_log.error("encountered empty highlight class: " + sline)
                    return scode
                else:
                    if sclass.lower() == "none":
                        # no highlighting wanted here.
                        lexer_ = None
                        formatter_ = None
                        sclass = ""
                    else:
                        # try highlighting with this lexer name.
                        try:
                            lexer_ = lexers.get_lexer_by_name(sclass)
                            formatter_ = formatters.html.HtmlFormatter(linenos=False, style="default")
                        except:
                            hl_log.error("highlight_inline: unable to create lexer/formatter with: " + sclass)
                            sclass = ""
                            lexer_ = None
                            formatter_ = None
                
                # don't attempt to highlight blocks where class is none.
                # its there for possible css styles/future development.
                inblock = not (sclass.lower() == "none")

                
    return sfinished


def get_embedded_lexer(scode):
    """ retrieves lexer name from embedded highlight line. """
    tag_match = re.search(r'\w+[ ]highlight-embedded|highlight-embedded[ ]\w+', scode)
    if tag_match is None:
        return None
    else:
        tag_list = tag_match.group().split(' ')
        return tag_list[1 - tag_list.index('highlight-embedded')]


def get_embedded_code(scode, tag_ = "span"):
    """ retrieves code content from embedded highlight line. """
    code_match = re.search(r'<' + tag_ + r' class\=["\'](\w+[ ]highlight-embedded|highlight-embedded[ ]\w+)["\']>(?P<content>.+)(?=</)', scode)
    if code_match is None:
        return None
    else:
        if len(code_match.groups()) < 2:
            return None
        else:
            return code_match.groups()[1]


def get_embedded_line(scode, tag_ = "span"):
    """ retrieves the whole embedded line, tags and all. """
    
    line_match = re.search(r'<' + tag_ + r' class\=["\'](\w+[ ]highlight-embedded|highlight-embedded[ ]\w+)["\']>.+</' + tag_ + '>', scode)
    if line_match is None:
        return None
    else:
        return line_match.group()

    
def get_embedded_content(sline, tag_ = "span"):
    """ retrieves lexer and code from a single embedded highlight line.
        returns tuple of (lexer name, code to highlight) strings.
        returns None on error.
    """
    
    lexer_name = get_embedded_lexer(sline)
    code_content = get_embedded_code(sline, tag_)
    whole_line = get_embedded_line(sline, tag_)
    return (lexer_name, code_content, whole_line)
    

def highlight_embedded(scode, tag_ = "span"):
    """ highlights embedded code, like:
        <p>
            To import the os module do <span class='highlight-embedded python'>import os</span> at the top of your script.
        </p>
        
        tag must have the 'highlight-embedded' class, and the lexer name as the other class.
    """
    
    if '\n' in scode:
        slines = scode.split('\n')
    else:
        # single line only.
        slines = [scode]
    
    keep_lines = []
    for sline in slines:
        if 'highlight-embedded' in sline:
            lexer_name, content_, whole_tag = get_embedded_content(sline)
            if (lexer_name is None) or (content_ is None) or (whole_tag is None):
                # error getting info from tag, use old line.
                keep_lines.append(sline)
            else:
                # highlight the embedded content.
                try:
                    lexer_ = lexers.get_lexer_by_name(lexer_name)
                    formatter_ = formatters.html.HtmlFormatter(linenos=False, nowrap=True, style='default')
                    highlighted = pygments.highlight(content_, lexer_, formatter_)
                    snewtag = "<" + tag_ + " class='highlighted-embedded'>" + highlighted + "</" + tag_ + ">"
                    # replace old content with new highlighted content.
                    snewline = sline.replace(whole_tag, snewtag)
                    keep_lines.append(snewline)
                except:
                    hl_log.debug("highlight_embedded: invalid lexer name in: " + whole_tag)
                    keep_lines.append(sline)
        else:
            # no embedding needed
            keep_lines.append(sline)   
            
    if len(keep_lines) == 1:
        return keep_lines[0]
    else:
        return "\n".join(keep_lines)
    
        
    
    
        

    
        