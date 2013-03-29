#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - search - tools
     @summary: provides various functions for searching welbornproductions
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 28, 2013
'''
# Safe to view generated html
from django.utils.safestring import mark_safe

# Project Info/Tools
from projects.models import wp_project
from projects import tools as ptools
# Blog Info/Tools
from blogger.models import wp_blog
from blogger import blogtools


class wp_result(object):
    """ holds search result information """
    
    def __init__(self, title_="", link_="", desc_="", posted_=""):
        self.title = title_
        self.link = link_
        self.description = mark_safe(desc_)
        self.posted = posted_


def search_projects(query_):
    """ search all wp_projects and return a list of results (wp_results).
        returns empty list on failure.
    """
    if query_ == "":
        return []
    
    if ' ' in query_:
        queries = query_.split(' ')
    else:
        queries = [query_]
        
    results = []
    for proj_ in wp_project.objects.order_by('-publish_date'):
        got_match = False
        pname = proj_.name
        palias = proj_.alias
        pver = proj_.version
        pdesc = proj_.description
        pdate = str(proj_.publish_date)
        pbody =  ptools.get_html_content(proj_)
        
        for query in queries:
            if ((query in pname) or
                (query in pver) or
                (query in pdesc) or
                (query in pdate) or
                (query in pbody)):
                # found match.
                got_match = True
        # Add this project if it matched any of the queries.
        if got_match:
            results.append(wp_result(title_ = pname + " v." + pver,
                                         desc_ = pdesc,
                                         link_ = '/projects/' + palias,
                                         posted_ = pdate))
    
    return results


def search_blog(query_):
    """ search all wp_blogs and return a list of results (wp_results).
        returns empty list on failure.
    """
    if query_ == "":
        return []
    
    if ' ' in query_:
        queries = query_.split(' ')
    else:
        queries = [query_]
        
    results = []
    for post_ in wp_blog.objects.order_by('-posted'):
        got_match = False
        ptitle = post_.title
        pslug = post_.slug
        pbody = blogtools.get_post_body(post_)
        pdesc = blogtools.prepare_content(blogtools.get_post_body_short(post_, max_text_lines=16))
        pdate = str(post_.posted)
        
        for query in queries:
            if ((query in ptitle) or
                (query in pslug) or
                (query in pbody) or
                (query in pdate)):
                got_match = True
        if got_match:
            results.append(wp_result(title_ = ptitle,
                                     desc_ = pdesc,
                                     link_ = "/blog/view/" + pslug,
                                     posted_ = pdate))
    return results


def search_all(query_, projects_first = True):
    """ searches both projects and blog posts """
    
    if projects_first:
        results = search_projects(query_)
        results += search_blog(query_)
    else:
        results = search_blog(query_)
        results += search_projects(query_)
    return results