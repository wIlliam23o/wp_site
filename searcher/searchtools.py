#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - search - tools
     @summary: provides various functions for searching welbornproductions
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 28, 2013
'''
# Global settings
from django.conf import settings
# Safe to view generated html
from django.utils.safestring import mark_safe
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger("welbornprod.search.tools", use_file=(not settings.DEBUG))
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
    if ((query_ == "") or
        (len(query_) < 3)):
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
            query = query.lower()
            
            if ((query in pname.lower()) or
                (query in pver) or
                (query in pdesc.lower()) or
                (query in pdate.lower()) or
                (query in pbody.lower())):
                # found match.
                got_match = True
        # Add this project if it matched any of the queries.
        if got_match:
            results.append(wp_result(title_ = pname + " v." + pver,
                                         desc_ = highlight_queries(queries, pdesc),
                                         link_ = '/projects/' + palias,
                                         posted_ = pdate))
    
    return results


def search_blog(query_):
    """ search all wp_blogs and return a list of results (wp_results).
        returns empty list on failure.
    """
    if ((query_ == "") or
        (len(query_) < 3)):
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
            query = query.lower()
            if ((query in ptitle.lower()) or
                (query in pslug.lower()) or
                (query in pbody.lower()) or
                (query in pdate.lower())):
                got_match = True
        if got_match:
            results.append(wp_result(title_ = ptitle,
                                     desc_ = highlight_queries(queries, pdesc),
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

def highlight_queries(queries_, scontent):
    """ makes all query words found in the content bold
        by wrapping them in a <strong> tag.
    """
    
    word_list = scontent.split(' ')
    if isinstance(queries_, (list, tuple)):
        queries = queries_
    else:
        if ',' in queries_: 
            queries_ = queries_.replace(',', ' ')
        if ' ' in queries_:
            queries = queries_.split(' ')
        else:
            queries = [queries_]
    # fix queries.
    queries_lower = [q.lower() for q in queries]
    # regex was not working for me. i'll look into it later.
    puncuation = ['.', ',', '!', '?', '+', '=', '-']
    for qcopy in [qc for qc in queries_lower]:
        for punc in puncuation:
            queries_lower.append(qcopy + punc)
            queries_lower.append(punc + qcopy)
            
        
            
    fixed_words = []
    for i in range(0, len(word_list)):
        word_ = word_list[i]
        word_lower = word_.lower()
        word_trim = word_lower.replace(',','').replace('.', '').replace(';', '').replace(':', '')
        fixed_word = word_
        for query in queries_lower:
            if ((query in word_lower) and
                (not "<strong>" in word_) and
                (not "</strong>" in word_)):
                # stops highlighting 'a' and 'apple' in 'applebaum'
                # when queries are: 'a', 'apple', 'applebaum'
                possible_fix = word_.replace(word_trim, "<strong>" + word_trim + "</strong>")
                if len(possible_fix) > len(fixed_word):
                    fixed_word = possible_fix
                    _log.debug("set possible: " + fixed_word)

        fixed_words.append(fixed_word)
    return ' '.join(fixed_words)

            