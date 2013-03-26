#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    utilities.py
    various tools/utilities for the welbornproductions.net django site..
    
    -Christopher Welborn
"""

import os.path
from os import walk #@UnusedImport: os.walk is used, aptana is stupid.
from django.conf import settings
#import logging
# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport
from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

# use log wrapper for debug and file logging.
from wp_logging import logger
_log = logger("welbornprod.utilities", use_file=True)



def get_request_arg(request, arg_name, default_value=None, min_val=0, max_val=9999):
    """ return argument from request (GET or POST),
        default value can be set.
        automatically returns int/float values instead of string where needed.
        min/max can be set for integer/float values.
    """
    
    try:
        val = request.REQUEST[arg_name]
    except:
        # no arg passed.
        val = ""
    
    if val.isalnum():
        # check min/max for int values
        try:
            int_val = int(val)
            if (int_val < min_val):
                int_val = min_val
            if (int_val > max_val):
                int_val = max_val
            # return float instead of string
            val = int_val
        except:
            pass
    else:
        # try float, check min/max if needed.
        try:
            float_val = float(val)
            if (float_val < min_val):
                float_val = min_val
            if (float_val > max_val):
                float_val = max_val
            # return float instead of string
            val = float_val
        except:
            pass
    
    # default value is empty string if none was passed.
    if default_value is None:
        default_value = ""    
    # final return after processing,
    # will goto default value if val is empty.
    if val == "":
        val = default_value
    return val
        
    
def wsgi_error(request, smessage):
    """ print message to requests wsgi errors """
    
    request.META['wsgi_errors'] = smessage
    
def remove_list_dupes(list_, max_allowed=1):
    """ removes duplicates from a list object.
        default allowed duplicates is 1, you can allow more if needed.
        minimum allowed is 1. this is not a list deleter.
    """
    
    for item_ in [item_copy for item_copy in list_]:
        while list_.count(item_) > max_allowed:
            list_.remove(item_)
    
    return list_

def prepend_path(prepend_this, prependto_path):
    """ os.path.join fails if prependto_path starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = prepend_path("/view" , project.source_dir)
    """
    
    spath = (prepend_this + prependto_path) if prependto_path.startswith('/') else (prepend_this + '/' + prependto_path)
    return spath.replace("//", '/')

def append_path(appendto_path, append_this):
    """ os.path.join fails if append_this starts with '/'.
        so I made my own. it's not as dynamic as os.path.join, but
        it will work.
        ex:
            mypath = append_path("/view" , project.source_dir)
    """
    
    spath = (appendto_path + append_this) if append_this.startswith('/') else (appendto_path + '/' + append_this)
    return spath.replace("//", '/')



def get_filename(file_path):
    try:
        sfilename = os.path.split(file_path)[1]
    except:
        _log.error("get_filename: error in os.path.split(" + file_path + ")")
        sfilename = file_path
    return sfilename
    
def safe_arg(_url):
    """ basically just trims the / from the POST args right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
    if s.startswith('/'):
        s = s[1:]
    return s


def trim_special(source_string):
    """ removes all html, and other code related special chars.
        so <tag> becomes tag, and javascript.code("write"); becomes javascriptcodewrite.
        to apply some sort of safety to functions that generate html strings.
        if someone did this: 
            welbornprod.com/blog/tag/<script type="text/javascript">document.write("d");</script>
        you're gonna have a bad time.
    """
    
    special_chars = "<>/.'" + '"' + "#!;:&"
    working_copy = source_string
    for char_ in source_string:
        if char_ in special_chars:
            working_copy = working_copy.replace(char_, '')
    return working_copy

            
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


def readmore_box(link_href):
    """ returns Html string for the readmore box. """
    
    return "<br/><a href='" + link_href + "'><div class='readmore-box'><span class='readmore-text'>more...</span></div></a>"


def comments_button(link_href):
    """ returns Html string for the comments box (button) """

    return "<a href='" + link_href + "#comments-box'><div class='comments-button'><span class='comments-button-text'>comments...</span></div></a>"
 
    
def is_file_or_dir(spath):
    """ returns true if path is a file, or is a dir. """
    
    return (os.path.isfile(spath) or os.path.isdir(spath))


def get_browser_name(request):
    """ return the user's browser name """
    
    # get user agent
    user_agent = get_user_agent(request)
    return user_agent.browser.family.lower()
    
def get_browser_style(request):
    """ return browser-specific css file (or False if not needed) """
    
    browser_name = get_browser_name(request)
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
    
    if relative_file_path == "":
        return ""
    
    sabsolutepath = ""
    for root, dirs, files in os.walk(settings.BASE_DIR): #@UnusedVariable: dirs, files
        spossible = os.path.join(root, relative_file_path)
        if os.path.isfile(spossible) or os.path.isdir(spossible):
            sabsolutepath = spossible
    return sabsolutepath

    
def load_html_file(sfile):
    """ loads html content from file.
        returns string with html content.
    """
    
    if not os.path.isfile(sfile):
        # try getting absolute path
        spath = get_absolute_path(sfile)
        if os.path.isfile(spath):
            sfile = spath
        else:
            # no file found.
            _log.debug("load_html_file: no file found at: " + sfile)
            return ""
        
    try:
        with open(sfile) as fhtml:
            return fhtml.read()
    except IOError as exIO:
        _log.error("load_html_file: \nCannot open file: " + sfile + '\n' + str(exIO))
        return ""
    except OSError as exOS:
        _log.error("load_html_file: \nPossible bad permissions opening file: " + sfile + '\n' + str(exOS))
        return ""
    except Exception as ex:
        _log.error("load_html_file: \nGeneral error opening file: " + sfile + '\n' + str(ex))
        return ""     
        

def check_replacement(source_string, target_replacement):
    """ fixes target replacement string in inject functions.
        if {{ }} was ommitted, it adds it.
        if {{target}} is in replacement instead of "{{ target }}",
        it fixes the target to match.
        otherwise, it returns the original target_replacement string.
    """
    
    # fix replacement if {{}} was omitted.
    if not target_replacement.startswith("{{"):
        target_replacement = "{{" + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + "}}"
        
    # this will look for '{{ target }}' and '{{target}}'...
    if target_replacement.replace(' ', '') in source_string:
        target_replacement = target_replacement.replace(' ', '')
        
    if target_replacement in source_string:
        return target_replacement
    else:
        _log.debug("fix_target_replacement: target not found in source string: " + target_replacement)
        return False
    


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
    
    # fail check.
    target = check_replacement(source_string, target_replacement)
    if not target:
        return source_string
        
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
        
    return source_string.replace(target, article_ad)



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
    target_replacement = check_replacement(source_string, target_replacement)
    if not target_replacement:
        return source_string
    if not os.path.isdir(images_dir):
        _log.debug("inject_screenshots: not a directory: " + images_dir)
        return source_string.replace(target_replacement, "")
    
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
        _log.debug("inject_screenshots: success.")
        return source_string.replace(target_replacement, sbase + spics + stail)


def inject_sourceview(project, source_string, link_text = None, desc_text = None, target_replacement = "{{ source_view }}"):
    """ injects code for source viewing.
        needs wp_project (project) passed to gather info.
        if target_replacement is not found, returns source_string.
    """

    # fail check.
    target = check_replacement(source_string, target_replacement)
    if not target:
        return source_string
    
    # has project info?
    if project is None:
        return source_string.replace(target, "")
    
    # get primary source file
    if project.source_file == "":
        srelativepath = get_relative_path(project.source_dir)
    else:
        srelativepath = get_relative_path(project.source_file)
    # has good link?
    if srelativepath == "":
        _log.debug("inject_sourceview: missing source file/dir for: " + project.name)
        return source_string.replace(target, "<span>Sorry, source not available for " + project.name + ".</span>")
    
    # link href
    slink = append_path("/view", srelativepath)
    
    # get link text
    if link_text is None:
        if project.source_file == "":
            link_text = "View Source (Local)"
        else:
            link_text = get_filename(project.source_file) + " (View Source)"
    # get description text
    if desc_text is None:
        desc_text = " - view source for " + project.name + " v." + project.version
    
    sbase = """<div class='source-view'>
                   <a class='source-view-link' href='{{ link }}'>{{ link_text }}</a>&nbsp;
                       <span class='source-view-text'>{{ desc_text }}</span>
               </div>
        """
    
    source_view = sbase.replace("{{ link }}", slink).replace("{{ link_text }}", link_text).replace("{{ desc_text }}", desc_text)
    return source_string.replace(target, source_view)
    
        
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
    
    ######## TEST TEST TEST 
    ilines = 0
    iprelines = 0
    
    # removes newlines, except for in pre blocks.
    if '\n' in source_string:
        in_pre = False
        final_output = []
        for sline in source_string.split('\n'):
            # start of pre tag
            if "<pre" in sline.lower():
                _log.debug("Found pre!: " + sline)
                in_pre = True
            # add content, keep newlines for pre.    
            if in_pre:
                _log.debug("keeping pre: " + sline)
                final_output.append(sline + '\n')
                iprelines += 1
            else:
                final_output.append(sline.replace('\n', ''))
                ilines += 1
            # end of tag
            if "</pre>" in sline.lower():
                _log.debug("End pre!: " + sline)
                in_pre = False
    else:
        ilines = 1
        final_output = [source_string]
    _log.debug("remove_newlines: processed " + str(ilines) + " regular lines,\n" + \
               "                 and " + str(iprelines) + " pre lines.")
    return "".join(final_output)

def remove_whitespace(source_string):
    """ removes leading and trailing whitespace from lines """
    
    if '\n' in source_string:
        keep_ = []
        for sline in source_string.split('\n'):
            keep_.append(sline.strip(' ').strip('\t'))
        return '\n'.join(keep_)
    else:
        return source_string


def hide_email(source_string):
    """ base64 encodes all email addresses for use with wptool.js reveal functions.
        for spam protection.
    """
    ##########################
    ##########################
    ##########################
    #@todo: Automatically base64 encode any href tag or innerHTML with .wp-address as the class
    ##########################
    pass
    
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

def alert_message(alert_message, body_message="<a href='/'><span>Click here to go home</span></a>", noblock=False):
    """ Builds an alert message, and returns the HttpResponse object. 
        alert_message: What to show in the alert box.
        body_message: Body content wrapped in a wp-block div.
                      Default is "Click here to go home."
        noblock: Don't wrap in wp-block div if True.
    
    """
    
    if noblock:
        main_content = body_message
    else:
        main_content = "<div class='wp-block'>" + body_message + "</div>"
    tmp_notfound = loader.get_template('home/main.html')
    cont_notfound = Context({'main_content': mark_safe(main_content),
                             'alert_message': mark_safe(alert_message),
                             })
    rendered = clean_template(tmp_notfound, cont_notfound, (not settings.DEBUG))
    return HttpResponse(rendered)

def render_response(template_name, context_dict):
    """ same as render_to_response, 
        loads template, renders with context,
        returns HttpResponse.
    """
    
    try:
        tmp_ = loader.get_template(template_name)
        cont_ = Context(context_dict)
        rendered = tmp_.render(cont_)
    except:
        rendered = alert_message("Sorry, there was an error loading this page.")
    return HttpResponse(rendered)

def clean_response(template_name, context_dict):
    """ same as render_response, except does code minifying/compression 
        (compresses only if settings.DEBUG=False)
        returns cleaned HttpResponse.
    """
    
    try:
        tmp_ = loader.get_template(template_name)
    except Exception as ex:
        _log.error("clean_response: could not load template: " + template_name + '<br/>\n' + \
                   str(ex))
        rendered = None
    else:
        try:
            cont_ = Context(context_dict)
        except Exception as ex:
            _log.error("clean_response: could not load context: " + str(context_dict) + "<br/>\n" + \
                       str(ex))
            rendered = None
        else:
            try:
                rendered = clean_template(tmp_, cont_, (not settings.DEBUG))
            except Exception as ex:
                _log.error("clean_response: could not clean_template!<br/>\n" + str(ex))
                rendered = None
    if rendered is None:
        return alert_message("Sorry, there was an error loaging this page.")
    else:
        return HttpResponse(rendered)


def redirect_response(redirect_to):
    """ returns redirect response.
        redirects user to redirect_to.
    """
    
    response = HttpResponse(redirect_to, status=302)
    response['Location'] = redirect_to
    return response
