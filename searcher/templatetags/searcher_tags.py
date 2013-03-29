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

register = template.Library()



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


register.filter("random_result_msg", random_result_msg)
    