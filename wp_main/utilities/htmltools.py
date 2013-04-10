#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - utilities - html
     @summary: provides html string manipulation, code injection/generation
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 27, 2013
'''


# Files/Paths 
import os.path

# Global settings
from django.conf import settings

# Regex for email hiding
import re 
import base64

# Basic utilities for strings/files/paths/whatever.
from wp_main.utilities import utilities

# Log
from wp_main.utilities.wp_logging import logger
_log = logger("welbornprod.utilities.html", use_file=(not settings.DEBUG))

# RegEx for finding an email address
re_email_address = r'[\d\w\-\.]+@[\d\w\-\.]+\.[\w\d\-\.]+'

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
 
    
def load_html_file(sfile):
    """ loads html content from file.
        returns string with html content.
    """
    
    if not os.path.isfile(sfile):
        # try getting absolute path
        spath = utilities.get_absolute_path(sfile)
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
        if "{{target}}" is in source_string instead of "{{ target }}",
        it fixes the target to match.
        if nothing is needed, it returns the original target_replacement string.
        if the target_replacement isn't in the source_string, it returns false,
        so use [if check_replacement()], not [if check_replacement() in source_string].
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
    

def inject_article_ad(source_string, target_replacement = "{{ article_ad }}"):
    """ basically does a text replacement, 
        replaces 'target_replacement' with the code for article ads.
        returns finished html string.
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
    #@todo: use regex to replace only words that aren't already wrapped in <strong>.
    #@todo: build common word list like Python,Linux,Windows,etc.
    if wordlist is None:
        wordlist = ['menuprops', 'MenuProps', 
                    'menu props', 'Menu Props',
                    ]
    for word_ in wordlist:
        if word_ in source_string:
            source_string = source_string.replace(word_, '<strong>' + word_ + '</strong>')
    return source_string


def inject_screenshots(source_string, images_dir, target_replacement = "{{ screenshots_code }}", 
                       noscript_image = None):
    """ inject code for screenshots box.
        walks image directory, building html for the image rotator box.
        examples:
            shtml = inject_screenshots(shtml, "static/images/myapp")
            shtml = inject_screenshots(shtml, "images/myapp/", noscript_image="sorry_no_javascript.png")
            shtml = inject_screenshots(shtml, "images/myapp", "{{ replace_with_screenshots }}", "noscript.png")
    """
    
    # fail checks, make sure target exists in source_string
    target_replacement = check_replacement(source_string, target_replacement)
    if not target_replacement:
        return source_string
    # get absolute path for images dir, if none exists then quit.
    images_dir = utilities.get_absolute_path(images_dir)
    if images_dir == "":
        return source_string.replace(target_replacement, "")
    
    # directory exists, now make it relative.
    relative_dir = utilities.get_relative_path(images_dir)
        
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
    
    # template for injecting image files
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
    # find acceptable pics
    good_pics = []
    for sfile in os.listdir(images_dir):
        if sfile[-3:].lower() in formats:
            good_pics.append(os.path.join(relative_dir, sfile))
    # no good pictures found?
    if len(good_pics) == 0:
        return source_string.replace(target_replacement, '')
    else:
        # found pics, process them.
        spics = ""
        for sfile in good_pics:
            spics += stemplate.replace('{{image_file}}', sfile)
        if noscript_image is None:
            noscript_image = good_pics[0]
        sbase = sbase.replace("{{noscript_image}}", noscript_image)
        return source_string.replace(target_replacement, sbase + spics + stail)


def inject_sourceview(project, source_string, link_text = None, desc_text = None, target_replacement = "{{ source_view }}"):
    """ injects code for source viewing.
        needs wp_project (project) passed to gather info.
        if target_replacement is not found, returns source_string.
        ** this probably needs to be in projects.tools **
    """

    # fail check.
    target = check_replacement(source_string, target_replacement)
    if not target:
        return source_string
    
    # has project info?
    if project is None:
        return source_string.replace(target, "")
    
    # use source_file if no source_dir was set.
    if project.source_dir == "":
        srelativepath = utilities.get_relative_path(project.source_file)
    else:
        srelativepath = utilities.get_relative_path(project.source_dir)
    # get default filename to display in link.
    if project.source_file == "":
        file_name = project.name
    else:
        file_name = utilities.get_filename(project.source_file)
            
    # has good link?
    if srelativepath == "":
        _log.debug("inject_sourceview: missing source file/dir for: " + project.name)
        return source_string.replace(target, "<span>Sorry, local source not available for " + project.name + ".</span>")
    
    # link href
    slink = utilities.append_path("/view", srelativepath)
    
    # get link text
    if link_text is None:
        if project.source_file == "":
            link_text = "View Source (Local)"
        else:
            link_text = file_name + " (View Source)"
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
            removes any line starting with <!-- and ending with -->. 
        """
            
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
    """ remove all newlines from a string 
        skips some tags, leaving them alone. like 'pre', so
        formatting doesn't get messed up.
    """
        
    # removes newlines, except for in pre blocks.
    if '\n' in source_string:
        in_skipped = False
        final_output = []
        for sline in source_string.split('\n'):
            sline_lower = sline.lower()
            # start of pre tag
            if (("<pre" in sline_lower) or
                ("<script" in sline_lower)):
                in_skipped = True
            # process line.  
            if in_skipped:
                # add original line.
                final_output.append(sline + '\n')
            else:
                # add trimmed line.
                final_output.append(sline.replace('\n', ''))
            # end of tag
            if (("</pre>" in sline_lower) or
                ("</script>" in sline_lower)):
                in_skipped = False
    else:
        final_output = [source_string]
    return "".join(final_output)


def remove_whitespace(source_string):
    """ removes leading and trailing whitespace from lines,
        and removes blank lines.

    """
    
    # removes newlines, except for in pre blocks.
    if '\n' in source_string:
        slines = source_string.split('\n')
    else:
        slines = [source_string]
    # start processing    
    in_skipped = False
    final_output = []
    for sline in slines:
        sline_lower = sline.lower()
        # start of skipped tag
        if "<pre" in sline_lower:
            in_skipped = True
        # process line.   
        if in_skipped:
            # add original line.
            final_output.append(sline)
        else:
            trimmed = trim_whitespace_line(sline)
            # no blanks.
            if trimmed != '\n' and trimmed != '':
                final_output.append(trimmed)
        # end of tag
        if "</pre>" in sline_lower:
            in_skipped = False

    return '\n'.join(final_output)



def trim_whitespace_line(sline):
    """ trims whitespace from a single line """
    
    scopy = sline
    while scopy.startswith(' ') or scopy.startswith('\t'):
        scopy = scopy[1:]
    while scopy.endswith(' ') or scopy.endswith('\t'):
        scopy = scopy[:-1]
    return scopy

def hide_email(source_string):
    """ base64 encodes all email addresses for use with wptool.js reveal functions.
        for spam protection.
    """
    
    if '\n' in source_string:
        slines = source_string.split('\n')
    else:
        # single line
        slines = [source_string]
    
    final_output = []
    for sline in slines:
        mailtos_ = find_mailtos(sline)
        for mailto_ in mailtos_:
            b64_mailto = base64.encodestring(mailto_).replace('\n','')
            sline = sline.replace(mailto_, b64_mailto )
            _log.debug("mailto: replaced " + mailto_ +'\n    with: ' + b64_mailto)
        emails_ = find_email_addresses(sline)
        for email_ in emails_:
            b64_addr = base64.encodestring(email_).replace('\n','')
            sline = sline.replace(email_, b64_addr )
            _log.debug("email: replaced " + email_ +'\n    with: ' + b64_addr)
        # add line (encoded or not)
        final_output.append(sline)
    return '\n'.join(final_output)


def find_mailtos(source_string):
    """ finds all instances of <a class='wp-address' href='mailto:email@adress.com'></a> for hide_email().
        returns a list of href targets ['mailto:name@test.com', 'mailto:name2@test2.com'],
        returns empty list on failure.
    
    """
    
    # regex pattern for finding href tag with 'mailto:??????' and a wp-address class
    s_mailto = r'<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address[\'"][ ]href[ ]?\=[ ]?["\']((mailto:)?' + re_email_address + ')'
    re_pattern = re.compile(s_mailto)
    raw_matches = re.findall(re_pattern, source_string)
    mailtos_ = []
    for groups_ in raw_matches:
        # first item is the mailto: line we want.
        mailtos_.append(groups_[0])
    return mailtos_


def find_email_addresses(source_string):
    """ finds all instances of email@addresses.com inside a wp-address classed tag. for hide_email() """
    
    # regex pattern for locating an email address.
    s_addr = r"(<\w+(?!>)[ ]class[ ]?\=[ ]?['\"]wp-address['\"])(.+)?[ >](" + re_email_address + ")"
    re_pattern = re.compile(s_addr)
    raw_matches = re.findall(re_pattern, source_string)
    addresses_ = []
    for groups_ in raw_matches:
        # the last item is the address we want
        addresses_.append(groups_[-1])
    return addresses_
