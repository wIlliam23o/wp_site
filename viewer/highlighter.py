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
                    try:
                        lexer_ = lexers.get_lexer_by_name(sclass)
                        formatter_ = formatters.html.HtmlFormatter(linenos=False, style="default")
                    except:
                        hl_log.error("highlight_inline: unable to create lexer/formatter with: " + sclass)
                        sclass = ""
                        lexer_ = None
                        formatter_ = None
                inblock = True
                
    return sfinished
    

    
        