#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - project tools
     @summary: provides tools for building html content related to projects
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 14, 2013
'''
# File/Path stuff
from os import listdir #@UnusedImport: os.listdir is used, aptana is stupid.
import os.path

# Project info
from projects.models import wp_project
# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import htmltools
# Code highlighting
#from wp_main.utilities.highlighter import highlight_inline, highlight_embedded
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger('projects.tools').log

def sorted_projects(sort_method = "-publish_date"):
    """ return sorted list of projects.
        sort methods: date, name, id
    """
    
    if sort_method.startswith("date") or sort_method.startswith("-date"):
        sort_method = "-publish_date"
        
    return [p for p in wp_project.objects.all().order_by(sort_method) if not p.disabled]


def get_screenshots_dir(project):
    """ determine screenshots directory for project """
    if project.screenshot_dir == "":
        # try default location
        images_dir = utilities.get_absolute_path("static/images/" + project.alias)
    else:
        if os.path.isdir(project.screenshot_dir):
            # project path was absolute
            images_dir = project.screenshot_dir
        else:
            # needs absolute?
            images_dir = utilities.get_absolute_path(project.screenshot_dir)
    return images_dir


def get_html_file(project):
    """ finds html file to use for project content, if any 
        returns empty string on failure.
    """
    
    if project.html_url == "":
        # use default location if no manual override is set.
        html_file = utilities.get_absolute_path("static/html/" + project.alias + ".html")
    elif project.html_url.lower() == "none":
        # html files can be disabled by putting None in the html_url field.
        return ""
    else:
        if os.path.isfile(project.html_url):
            # already absolute
            html_file = project.html_url
        else:
            # try absolute path
            html_file = utilities.get_absolute_path(project.html_url)
    return html_file


def get_html_content(project):
    """ retrieves extra html content for project, if any """
    
    sfile = get_html_file(project)
    shtml = htmltools.load_html_file(sfile)
    
    if shtml == "":
        _log.debug("missing html for " + project.name + ": " + sfile)
    
    return shtml

    
def get_download_file(project):
    """ determines location of download file, 
        or returns empty string if we can't find it anywhere. """
    
    surl = project.download_url
    if surl == "":
        return ""
    if utilities.is_file_or_dir(surl):
        # already absolute
        return surl
    else:
        # try absolute_path
        return utilities.get_absolute_path(surl)
       

def get_download_content(project):
    """ retrieve download content for project.
        if single file is listed in download_url, we'll use that.
        if single file is an html file, we'll load the html from it.
        if directory is listed, we'll list all files.
        if nothing is listed, we won't show anything.
    """
    
    surl = get_download_file(project)
    if surl == "":
        scontent = ""
    else:
        if os.path.isfile(surl):
            scontent = get_download_file_content(project, surl)
        elif os.path.isdir(surl):
            scontent = get_download_dir_content(project, surl)
        else:
            scontent = ""
    return scontent


def get_download_file_content(project, surl):
    """ gets download content, 
        if surl is an html file it loads the content.
        if surl is any other file it builds a download box using
        surl as the target download.
    """
    
    if surl.lower().endswith('.html') or surl.lower().endswith('.htm'):
        return htmltools.load_html_file(surl)
    else:
        # intialize with download-list div
        html_ = htmltools.html_content("<div class='wp-block download-list'>")
        # build html for download link
        html_.append_lines((build_download_file_content(project, surl), '</div>'))
        return html_.tostring()
    
    
def build_download_file_content(project, surl, desc_text = ' - Current package.'):
    """ builds download content box from single file url.
        given the file to download, it outputs the html for the
        download section.
    """
    
    # intial template for this downloadable file link    
    html_ = htmltools.html_content("""
        <div class='download-file'>
            <a class='download-link' href='{{ relative_link }}'>
                <span class='download-link-text'>{{ link_text }}</span>
            </a>
            <span class='download-desc'>&nbsp;{{ desc_text }}</span>
        </div>""")
    
    # make link
    html_.replace('{{ relative_link }}', '/dl' + utilities.get_relative_path(surl))
    # make desc text
    html_.replace('{{ desc_text }}', desc_text)
    # make link text
    sver = project.version
    if sver == "":
        slinktext = project.name
    else:
        slinktext = project.name + ' v' + sver
    html_.replace('{{ link_text }}', slinktext)
    
    return html_.tostring()

    
def get_download_dir_content(project, surl):
    """ builds download content box from url.
        full dir list mode.
    """
    
    if not os.path.isdir(surl):
        return ""
    
    try:
        files = os.listdir(surl)
    except Exception as ex:
        _log.error("unable to list dir: " + surl + '\n' + str(ex))
        return ""

    # intialize with head for download content
    html_ = htmltools.html_content("<div class='wp-block download-list'>")

    for sfile in files:
        spath = os.path.join(surl, sfile)
        # add this file to content
        html_.append_line(build_download_file_content(project, spath, ""))
    # add tail to download content
    html_.append_line('</div>')

    return html_.tostring()
    

def prepare_content(project, scontent):
    """ prepares project content for final view.
        adds screenshots, downloads, ads, etc.
        returns injected html string.
    """
    
    # Top of page. Includes project name header.
    shead = "<div class='project_container'>\n" + \
        "    <div class='project_title'>\n" + \
        "        <h1 class='project-header'>" + project.name + "</h1>\n" + \
        "    </div>\n"
    # Working copy of html content
    html_ = htmltools.html_content(scontent)
    
    # do article ads.
    html_.inject_article_ad()
        
    # do screenshots.
    images_dir = get_screenshots_dir(project)
    # inject screenshots.      
    if os.path.isdir(images_dir):
        html_.inject_screenshots(images_dir)
        
    # do downloads.
    sdownload_content = get_download_content(project)
    if sdownload_content != "":
        target_ = html_.check_replacement("{{ download_code }}")
        html_.replace_if(target_, sdownload_content)
            
    # do source view.
    html_.inject_sourceview(project)

    # do auto source highlighting
    html_.highlight()
 
    # remember to close the project_container div.
    html_.prepend(shead)
    html_.append('\n</div>\n')
    
    # returning STRING until the rest of the project starts using html_content.
    return html_.tostring()


def process_injections(project, request=None):
    """ Replaces target strings {{ article_ad }}, {{ source_view }}, etc.
        with the proper code per project.
        Returns projects description (string) in html format.
    """
    
    try:
        html_ = htmltools.html_content(get_html_content(project))
    except Exception as ex:
        _log.debug("Error getting html content:\n" + str(ex))
        return ""
    
    try:
        html_.inject_article_ad()
        html_.inject_sourceview(project, request=request)
    except Exception as ex:
        _log.debug("Error injecting article_ad/sourceview:\n" + str(ex))
        return ""
    
    try:
        download_code = get_download_content(project)
        if download_code:
            target = html_.check_replacement("{{ download_code }}")
            html_.replace_if(target, download_code)
    except Exception as ex:
        _log.debug("Error injecting download code:\n" + str(ex))
        return ""
    
    try:
        screenshots_dir = get_screenshots_dir(project)
        if os.path.isdir(screenshots_dir):
            html_.inject_screenshots(screenshots_dir)
    except Exception as ex:
        _log.debug("Error injecting screenshots code:\n" + str(ex))
        return ""
    
    try:
        html_.highlight()
    except Exception as ex:
        _log.debug("Error injecting highlights:\n" + str(ex))
        return ""
    
    return html_.tostring()


    
def get_project_from_path(file_path):
    """ determines if this file is from a project. 
        returns project object if it is.
        returns None on failure.
    """
    
    # check all project names
    for proj in [p for p in wp_project.objects.all() if not p.disabled]:
        if proj.alias in str(file_path):
            return proj
    return None

    
