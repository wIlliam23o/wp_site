#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    utilities.py
    various tools/utilities for the welbornproductions.net django site..
    
    -Christopher Welborn
"""

import os, os.path
from django.conf import settings


def inject_custom(source_string):
    """ runs all custom injection functions with default settings. """
    
    # so far just the one function.
    custom_replacements = [inject_article_ad]
    
    for replacement_function in custom_replacements:
        source_string = replacement_function(source_string)
        
    return source_string
  
    
def inject_article_ad(source_string, target_replacement = "{{ article_ad }}"):
    """ basically does a text replacement, 
        replaces 'target_replacement' with 'article_ad'.
        returns finished string.
        ex:
            # looks for {{ ad }}, and {{ad}} to replace.
            shtml = inject_article_ad(shtml, "{{ ad }}")
            -or-
            # automatically wraps target in {{}} if it was omitted.
            shtml = inject_article_ad(shtml, "ad")
    """
    
    # fix replacement if {{}} was omitted.
    if not target_replacement.startswith("{{"):
        target_replacement = "{{" + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + "}}"
        
    # this will look for '{{ target }}' and '{{target}}'...
    if not target_replacement in source_string:
        target_replacement = target_replacement.replace(' ', '')
        
    article_ad = """
        <div class='article-ad'>
            <script type='text/javascript'>
                <!--
                google_ad_client = 'ca-pub-0811371441457236';
                /* LeaderBoard-InsideArticles */
                google_ad_slot = '7930726415';
                google_ad_width = 728;
                google_ad_height = 90;
                //-->
            </script>
            <script type='text/javascript'
                     src='http://pagead2.googlesyndication.com/pagead/show_ads.js'>
            </script>
        </div>"""
        
    if target_replacement in source_string:
        return source_string.replace(target_replacement, article_ad)
    else:
        return source_string


def inject_bold_words(source_string, wordlist = None):
    """ wrap all words in wordlist with <strong> tag.
        case-sensative when matching.
        if wordlist is None, default words will be used.
        returns finished string.
    """
    
    # experimental, needs some regex...
    if wordlist is None:
        wordlist = ['menuprops', 'MenuProps', 
                    'menu props', 'Menu Props',
                    ]
    for word_ in wordlist:
        if word_ in source_string:
            source_string = source_string.replace(word_, '<strong>' + word_ + '</strong>')
    return source_string


def inject_screenshots(source_string, images_dir, target_replacement = "{{ screenshots_code }}", noscript_image = None):
    """ inject code for screenshots box.
        walks image directory, building html for the image rotator box.
        examples:
            shtml = inject_screenshots(shtml, "/static/images/myapp")
            shtml = inject_screenshots(shtml, "/images/myapp/", noscript_image="sorry_no_javascript.png")
            shtml = inject_screenshots(shtml, "/images/myapp", "{{ replace_with_screenshots }}", "noscript.png")
    """
    
    # fail checks.
    if not os.path.isdir(images_dir):
        return source_string
    if not target_replacement.startswith("{{"):
        target_replacement = "{{" + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + "}}"
    if not target_replacement in source_string:
        if target_replacement.replace(' ', '') in source_string:
            target_replacement = target_replacement.replace(' ', '')
        else:
            return source_string
    
    # directory exists, now make it relative.
    if "/static" in images_dir:
        relative_dir = images_dir[images_dir.index("/static"):]
    else:
        relative_dir = images_dir
        
    # start of rotator box
    sbase = """
    <div class="screenshots_box">
        <div class="wt-rotator">
            <div class="screen">
                <noscript>
                    <!-- placeholder 1st image when javascript is off -->
                    <img src="{{noscript_image}}"/>
                </noscript>
              </div>
            <div class="c-panel">
                  <div class="thumbnails">
                    <ul>
    """
    # end of rotator box
    stail = """                      </ul>
                 </div>     
                  <div class="buttons">
                    <div class="prev-btn"></div>
                    <div class="play-btn"></div>    
                    <div class="next-btn"></div>               
                </div>
            </div>
        </div>    
    </div>
    """
    
    # template for inecting image files
    stemplate = """
                        <li>
                            <a href="{{image_file}}" title="screen shots">
                                <img class="screenshot" src="{{image_file}}"/>
                            </a>
                            <a href="{{image_file}}" target="_blank"></a>                        
                        </li>
                """
    
    # accceptable image formats
    formats = ["png", "jpg", "gif", "bmp"]
    # acceptable pics
    good_pics = []
    for sfile in os.listdir(images_dir):
        if sfile[-3:].lower() in formats:
            good_pics.append(os.path.join(relative_dir, sfile))
    
    if len(good_pics) == 0:
        return source_string.replace(target_replacement, '')
    else:
        spics = ""
        for sfile in good_pics:
            spics += stemplate.replace('{{image_file}}', sfile)
        if noscript_image is None:
            noscript_image = good_pics[0]
        sbase = sbase.replace("{{noscript_image}}", noscript_image)
        return source_string.replace(target_replacement, sbase + spics + stail)

def remove_comments(source_string):
    """ splits source_string by newlines and 
        removes any line starting with <!-- and ending with -->. """
        
    if (not "<!--" in source_string) or (not '\n' in source_string):
        return source_string
    
    slines = source_string.split('\n')
    keeplines = []
    
    for sline in slines:
        strim = sline.replace('\t', '').replace(' ','')
        if (not (strim.startswith("<!--") and 
                 strim.endswith("-->"))):
            keeplines.append(sline)
    
    return '\n'.join(keeplines)
  
