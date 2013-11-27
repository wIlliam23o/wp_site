#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - searcher - template tags
     @summary: provides various functions for the search pages
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 29, 2013
'''
import random
from django import template
from django.utils.safestring import mark_safe
from wp_main.utilities import highlighter

register = template.Library()


def highlight_desc(s):
    """ Runs all description text through highlight_codes. """

    if s:
        s = highlighter.highlight_codes(s)
    return mark_safe(s)


def random_result_msg(value):
    """ the value really doesn't matter,
        this returns a random message for:
        "Sorry no results were found,"
        [insert message here]
    """
    
    sorry_msgs = ["Maybe try a different wording?",
                  "Maybe it's under a different name?",
                  "You could try browsing all of my projects. :)",
                  "You could try browsing my blog :)",
                  "Did you check your spelling?",
                  "You can try entering something else.."]
    
    return sorry_msgs[random.randint(0, len(sorry_msgs) - 1)]

# Which functions should be registered as tags
registered = (highlight_desc,
              random_result_msg,
              )
# Register all functions in the registered list.
for func in registered:
    register.filter(func.__name__, func)
