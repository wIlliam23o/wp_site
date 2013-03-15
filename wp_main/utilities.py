#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    utilities.py
    various tools/utilities for the welbornproductions.net django site..
    
    -Christopher Welborn
"""

import os.path
from os import walk
from django.conf import settings
import logging
# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport

wp_log = logging.getLogger('welbornprod.utilities')

def safe_arg(_url):
    """ basically just trims the / from the args right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
    if s.startswith('/'):
        s = s[1:]
    return s


def wrap_link(content_, link_url, alt_text = ""):
    """ wrap content in <a href> """
    s = ""
    s_end = ""
    if link_url != "":
        s = "<a href='" + link_url + "'"
        if alt_text != "":
            s += " alt='" + alt_text + '"'
        s += ">"
        s_end = "</a>"
    
    return s + content_ + s_end


def is_file_or_dir(spath):
    """ returns true if path is a file, or is a dir. """
    
    return (os.path.isfile(spath) or os.path.isdir(spath))


def get_browser_style(request):
    """ return browser-specific css file (or False if not needed) """
    # get user agent
    user_agent = get_user_agent(request)
    browser_name = user_agent.browser.family.lower()
    # get browser css to use...
    if browser_name.startswith("ie"):
        return "/static/css/main-ie.css"
    elif "firefox" in browser_name:
        return "/static/css/main-gecko.css"
    elif "chrome" in browser_name:
        return "/static/css/main-webkit.css"
    else:
        return False
    


def get_relative_path(spath):
    """ removes base path to make it django-relative.
        if its a '/static' related dir, just trim up to '/static'.
    """
    
    if settings.BASE_DIR in spath:
        spath = spath.replace(settings.BASE_DIR, '')
    
    # if static file, just make it a '/static/...' path.
    if '/static' in spath:
        spath = spath[spath.index('/static'):]
    return spath


def get_absolute_path(relative_file_path):
    """ return absolute path for file, if any
        returns empty string on failure.
    """
    
    for root, dirs, files in os.walk(settings.BASE_DIR): #@UnusedVariable: dirs, files
        sabsolute = os.path.join(root, relative_file_path)
        if os.path.isfile(sabsolute):
            return sabsolute
    return ""

    
def load_html_file(sfile):
    """ loads html content from file.
        returns string with html content.
    """
    
    if not os.path.isfile(sfile):
        # try adding base dir
        spath = os.path.join(settings.BASE_DIR, sfile)
        if os.path.isfile(spath):
            sfile = spath
        else:
            # no file found.
            wp_log.debug("load_html_file: no file found at: " + sfile)
            return ""
        
    try:
        with open(sfile) as fhtml:
            return fhtml.read()
    except IOError as exIO:
        wp_log.error("load_html_file: \nCannot open file: " + sfile + '\n' + str(exIO))
        return ""
    except OSError as exOS:
        wp_log.error("load_html_file: \nPossible bad permissions opening file: " + sfile + '\n' + str(exOS))
        return ""
    except Exception as ex:
        wp_log.error("load_html_file: \nGeneral error opening file: " + sfile + '\n' + str(ex))
        return ""     
        
def inject_text(source_string, target_replacement, replace_with):
    """ basic text replacement, replaces target_replacement with replace_with. """
    
    if target_replacement in source_string:
        return source_string.replace(target_replacement, replace_with)
    else:
        return source_string
    
     
def inject_all(source_string):
    """ runs all custom injection functions with default settings. """
    
    # so far just the one function.
    custom_replacements = [inject_article_ad,
                           inject_screenshots]
    
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
        wp_log.debug("inject_screenshots: not a directory: " + images_dir)
        return source_string
    if not target_replacement.startswith("{{"):
        target_replacement = "{{" + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + "}}"
    if not target_replacement in source_string:
        if target_replacement.replace(' ', '') in source_string:
            target_replacement = target_replacement.replace(' ', '')
        else:
            wp_log.debug("inject_screenshots: replacement string not found: " + target_replacement)
            return source_string
    
    # directory exists, now make it relative.
    relative_dir = get_relative_path(images_dir)
        
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
        wp_log.debug("inject_screenshots: success.")
        return source_string.replace(target_replacement, sbase + spics + stail)

def remove_comments(source_string):
        """ splits source_string by newlines and 
            removes any line starting with <!-- and ending with -->. """
            
        if ("<!--" in source_string) and ('\n' in source_string):
            keeplines = []
            
            for sline in source_string.split('\n'):
                strim = sline.replace('\t', '').replace(' ','')
                if not (strim.startswith("<!--") and strim.endswith("-->")):
                    keeplines.append(sline)

            return '\n'.join(keeplines)
        else:
            return source_string

def remove_newlines(source_string):
    """ remove all newlines from a string """
    
    return source_string.replace('\n', '')

def remove_whitespace(source_string):
    """ removes leading and trailing whitespace from lines """
    
    if '\n' in source_string:
        keep_ = []
        for sline in source_string.split('\n'):
            keep_.append(sline.strip(' ').strip('\t'))
        return '\n'.join(keep_)
    else:
        return source_string
    
def clean_template(template_, context_, force_ = False):
    """ renders a template with context and 
        applies the cleaning functions.
        if DEBUG = True then only comments are removed.
    """
    
    if ((settings.DEBUG == True) and (force_ == False)):
        return remove_comments(template_.render(context_))
    else:
        # operations must be performed in this order.
        return remove_newlines(
                    remove_whitespace(
                    remove_comments(
                    template_.render(context_))))
