#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - project tools
     @summary: provides tools for building html content related to projects
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 14, 2013
'''
from os import listdir #@UnusedImport: os.listdir is used, aptana is stupid.
import os.path
from django.conf import settings
from projects.models import wp_project
from wp_main import utilities
import logging

tools_log = logging.getLogger('welbornprod.projects.tools')

def sorted_projects(sort_method = "date"):
    """ return sorted list of projects.
        sort methods: date, name, id
    """
    
    if sort_method == "date":
        sort_method = "publish_date"
        
    return wp_project.objects.all().order_by(sort_method)

     
def get_matches_html(project, requested_page):
    """ returns Html code for project matches, or 'sorry' html if no matches """

    # initial html, no project found, not a list.
    shtml = "<span>Sorry, no matching projects found for: " + requested_page + "</span>"
    
    if isinstance(project, list):
        if len(project) > 0:
            # build possible matches..
            shtml = "<div class='surround_matches'>" + \
                "<span>Sorry, I can't find a project at '" + requested_page + "'. Were you " + \
                "looking for one of these?</span><br/>" + \
                "<div class='project_matches'>"
            for proj in project:
                shtml += "<div class='project_match'>"
                p_name = "<span class='match_result'>" + \
                         proj.name + "</span>"
                p_link = "/projects/" + proj.alias
                shtml += utilities.wrap_link(p_name, p_link) + \
                     "</div>"
            shtml += "</div></div>"
    return shtml


def get_screenshots_dir(project):
    """ determine screenshots directory for project """
    if project.screenshot_dir == "":
        # try default location
        images_dir = os.path.join(settings.BASE_DIR, "projects/static/images/" + project.alias)
    else:
        if os.path.isdir(project.screenshot_dir):
            # project path was absolute
            images_dir = project.screenshot_dir
        else:
            # needs base dir added?
            images_dir = os.path.join(settings.BASE_DIR, project.screenshot_dir)
    return images_dir


def get_html_file(project):
    """ finds html file to use for project content, if any """
    
    if project.html_url == "":
        html_file = os.path.join(settings.BASE_DIR, "projects/static/html/" + project.alias + ".html")
        tools_log.debug("get_html_file: no html_url set, trying: " + html_file)
    else:
        if os.path.isfile(project.html_url):
            html_file = project.html_url
        else:
            # try adding base dir.
            html_file = os.path.join(settings.BASE_DIR, project.html_url)
    return html_file

def get_html_content(project):
    """ retrieves extra html content for project, if any """
    
    sfile = get_html_file(project)
    shtml = utilities.load_html_file(sfile)
    
    if shtml == "":
        tools_log.debug("get_html_content: missing html for " + project.name + ": " + sfile)
    
    return shtml

    
def get_download_file(project):
    """ determines location of download file, 
        or returns empty string if we can't find it anywhere. """
    
    surl = project.download_url
    if surl == "":
        return ""
    if utilities.is_file_or_dir(surl):
        return surl
    else:
        # try adding base dir
        spath = os.path.join(settings.BASE_DIR, surl)
        if utilities.is_file_or_dir(spath):
            return spath
    return ""

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
        return utilities.load_html_file(surl)
    else:
        shead = "<div class='wp-block download-list'>\n"
        stail = '</div>'
        return shead + build_download_file_content(project, surl) + stail
    
    
def build_download_file_content(project, surl, desc_text = ' - Current package.'):
    """ builds download content box from single file url.
        given the file to download, it outputs the html for the
        download section.
    """
        
    sbase = """
        <div class='download-file'>
            <a class='download-link' href="{{ relative_link }}">
                <span class='download-link-text'>{{ link_text }}</span>
            </a>
            <span class='download-desc'>&nbsp;{{ desc_text }}</span>
        </div>
    """
    # make link
    sbase = sbase.replace('{{ relative_link }}', '/dl' + utilities.get_relative_path(surl))
    # make desc text
    sbase = sbase.replace("{{ desc_text }}", desc_text)
    # make link text
    sver = project.version
    if sver == "":
        slinktext = project.name
    else:
        slinktext = project.name + ' v' + sver
    return sbase.replace('{{ link_text }}', slinktext)

    
def get_download_dir_content(project, surl):
    """ builds download content box from url.
        full dir list mode.
    """
    
    if not os.path.isdir(surl):
        return ""
    
    try:
        files = os.listdir(surl)
    except Exception as ex:
        tools_log.error("get_download_dir_content: unable to list dir: " + surl + '\n' + str(ex))
        return ""

    shead = "<div class='wp-block download-list'>\n"
    stail = '</div>'
    content_ = ""
    for sfile in files:
        spath = os.path.join(surl, sfile)
        content_ += build_download_file_content(project, spath, "")
    
    return shead + content_ + stail
    

def get_projects_menu(max_length = 25, max_text_length = 14):
    """ build a vertical projects menu from all wp_projects """
    
    if wp_project.objects.count() == 0:
        return ""
    
    shead = "<div class='vertical-menu'>\n" + \
            "<ul class='vertical-menu-main'>\n"
    stail = "</ul>\n</div>\n"
    stemplate = """
                    <li class='vertical-menu-item'>
                        <a class='vertical-menu-link' href='/projects/{{ alias }}'>
                            <span class='vertical-menu-text'>{{ name }}</span>
                        </a>
                    </li>
    """
    smenu = ""
    icount = 0
    for proj in wp_project.objects.all().order_by('name'):
        stext = proj.name
        if len(stext) > max_text_length:
            if len(proj.alias) > max_text_length:
                stext = proj.alias[:max_text_length - 3] + "..."
            else:
                stext = proj.alias
        
        smenu += stemplate.replace("{{ alias }}", proj.alias).replace("{{ name }}", stext)
        icount += 1
        if icount > max_length:
            break
        
    return shead + smenu + stail


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
    # Working copy
    shtml = scontent
    # do article ads.
    shtml = utilities.inject_article_ad(shtml)
        
    # do screenshots.
    images_dir = get_screenshots_dir(project)
    tools_log.debug("trying screenshots_dir: " + images_dir)
    # inject screenshots.            
    if os.path.isdir(images_dir):
        tools_log.debug("using screenshot_dir: " + images_dir)
        shtml = utilities.inject_screenshots(shtml, images_dir)
    else:
        if images_dir == "":
            tools_log.debug("No screenshots_dir specified.")
        else:
            tools_log.debug("screenshots_dir doesn't exist!: " + images_dir)
    
    # do downloads.
    sdownload_content = get_download_content(project)
    if sdownload_content != "":
        shtml = utilities.inject_text(shtml, "{{ download_code }}", sdownload_content)
    
    # do source view.
    shtml = utilities.inject_sourceview(project, shtml)
    
    # do auto source highlighting
    if "<pre class=" in shtml:
        from viewer.highlighter import highlight_inline
        shtml = highlight_inline(shtml)
    if "highlight-embedded" in shtml:
        from viewer.highlighter import highlight_embedded
        shtml = highlight_embedded(shtml)
        
    # remember to close the project_container div.
    return shead + shtml + "\n</div>\n"


def get_project_from_path(file_path):
    """ determines if this file is from a project. 
        returns project object if it is.
        returns None on failure.
    """
    
    # check all project names
    for proj in wp_project.objects.all():
        if proj.alias in str(file_path):
            return proj
    return None

    
