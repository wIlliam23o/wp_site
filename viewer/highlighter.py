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
            highlighted = "<div class='highlighted'>" + pygments.highlight(self.code, self.lexer, self.formatter) + "</div>"
        except:
            highlighted = ""
        return highlighted

    def get_styledefs(self):
        """ return css style definitions (for debugging really) """
        
        return self.formatter.get_style_defs()
    
        