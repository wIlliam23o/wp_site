#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welborn productions - search - tools
     @summary: provides various functions for searching welbornproductions
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 28, 2013
'''
# Global settings
#from django.conf import settings
# Safe to view generated html
from django.utils.safestring import mark_safe
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger("search.tools").log

# Project Info/Tools
from projects.models import wp_project
from projects import tools as ptools
# Blog Info/Tools
from blogger.models import wp_blog
from blogger import blogtools
# Misc Info
from misc.models import wp_misc
from misc import tools as misctools
# App Info
from apps.models import wp_app


class WpResult(object):

    """ holds search result information """
    # A map to type aliases and proper names for result types.
    types = {
        'post': 'Blog Post',
        'project': 'Project',
        'misc': 'Misc.',
        'app': 'Web App.',
        'none': '',
    }

    def __init__(self, title='', link='', desc='', posted='', restype=''):
        # Title for the link that is generated in this result.
        self.title = title
        # Link href for this result.
        self.link = link
        # Small description for this result.
        self.description = mark_safe(desc)
        # Publish date for this result.
        self.posted = posted
        # Type of result (project, blog post, misc, etc.)
        if restype in WpResult.types:
            self.restype = WpResult.types[restype]
        else:
            self.restype = WpResult.types['none']


def fix_query_string(querystr):
    """ Removes too many spaces from query string. """
    if not hasattr(querystr, 'encode'):
        querystr = str(querystr)

    while '  ' in querystr:
        querystr = querystr.replace('  ', ' ')
    while '++' in querystr:
        querystr = querystr.replace('++', '+')
        
    return querystr


def force_query_list(querystr):
    """ If string is passed with ' ', does string.split(),
        if string is passed without ' ', [string] is returned.
        any queries with len(replace(' ', '')) < 3 are culled.
        ...basically forces the use of a list.
    """

    if not hasattr(querystr, 'encode'):
        querystr = str(querystr)
    
    # string with ' '
    if ' ' in querystr:
        return [q for q in querystr.split(' ') if len(q.replace(' ', '')) > 2]
    # string, no spaces
    return [querystr]

  
def has_illegal_chars(querystr):
    """ check for illegal characters in query,
        returns True on first match, otherwise False.
    """
    
    illegalchars = (':', '<', '>', ';', 'javascript:', '{', '}', '[', ']')
    for char in illegalchars:
        #_log.debug("checking " + char_ + " in " + query_.replace(' ', ''))
        if char in querystr.replace(' ', ''):
            return True
        
    return False


def highlight_queries(queriestr, scontent):
    """ makes all query words found in the content bold
        by wrapping them in a <strong> tag.
    """
    
    word_list = scontent.split(' ')
    if isinstance(queriestr, (list, tuple)):
        queries = queriestr
    else:
        if ',' in queriestr:
            queriestr = queriestr.replace(',', ' ')
        if ' ' in queriestr:
            queries = queriestr.split(' ')
        else:
            queries = [queriestr]
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
        # Remove certain characters from the word and save to word_trim.
        word_trim = word_lower
        for c in ',.;:"\'':
            word_trim = word_trim.replace(c, '')

        fixed_word = word_
        for query in queries_lower:
            if len(query.replace(' ', '')) > 1:
                # contains query
                if ((query in word_lower) and
                   # not words that are already bold
                   (not "<strong>" in word_) and
                   (not "</strong>" in word_) and
                   # not words that may be html tags
                   (not (word_.count('=') and word_.count('>')))):

                    # stops highlighting 'a' and 'apple' in 'applebaum'
                    # when queries are: 'a', 'apple', 'applebaum'
                    boldword = '<strong>{}</strong>'.format(word_trim)
                    possible_fix = word_.replace(word_trim, boldword)
                    if len(possible_fix) > len(fixed_word):
                        fixed_word = possible_fix
                        #_log.debug("set possible: " + fixed_word)

        fixed_words.append(fixed_word)
    return ' '.join(fixed_words)


def is_empty_query(querystring):
    """ returns True if querystring == '', or len(querystring) < 3 """

    if not hasattr(querystring, 'encode'):
        querystring = str(querystring)
    return (querystring == '') or (len(querystring) < 3)


def search_all(querystr, projects_first=True):
    """ searches both projects and blog posts """
    
    if projects_first:
        results = search_projects(querystr)
        results.extend(search_apps(querystr))
        results.extend(search_misc(querystr))
        results.extend(search_blog(querystr))
    else:
        results = search_blog(querystr)
        results.extend(search_projects(querystr))
        results.extend(search_apps(querystr))
        results.extend(search_misc(querystr))
    return results


def search_apps(querystr):
    """ search all wp_app objects and return a list of results (WpResults).
        returns empty list on failure.
    """
    if is_empty_query(querystr):
        return []

    # Forces list, and trims queries len > 2.
    queries = force_query_list(querystr)
    if not queries:
        # empty queries, or too short queries in the string.
        return []

    if not wp_app.objects.count():
        # Nothing to search.
        return []

    results = []
    for app in wp_app.objects.filter(disabled=False).order_by('-publish_date'):
        acontent = app.description
        targets = (app.name, app.alias,
                   app.version, app.description,
                   str(app.publish_date),
                   )
        got_match = search_targets(queries, targets)
        if got_match:
            goodresult = WpResult(title=app.name,
                                  desc=highlight_queries(queries,
                                                         acontent),
                                  link='/apps/{}'.format(app.alias),
                                  posted=str(app.publish_date),
                                  restype='app')
            results.append(goodresult)
    return results


def search_blog(querystr):
    """ search all wp_blogs and return a list of results (WpResults).
        returns empty list on failure.
    """
    if is_empty_query(querystr):
        return []
    
    queries = force_query_list(querystr)
    
    if not wp_blog.objects.count():
        # Nothing to search
        return []
    
    results = []
    for post in wp_blog.objects.filter(disabled=False).order_by('-posted'):
        praw = blogtools.get_post_body_short(post, max_text_lines=16)
        pdesc = blogtools.prepare_content(praw)
        targets = (post.title, post.slug,
                   blogtools.get_post_body(post), pdesc,
                   str(post.posted),
                   )

        got_match = search_targets(queries, targets)
        if got_match:
            results.append(WpResult(title=post.title,
                                    desc=highlight_queries(queries, pdesc),
                                    link="/blog/view/" + post.slug,
                                    posted=str(post.posted),
                                    restype='post'))
    return results


def search_misc(querystr):
    """ search all wp_misc objects and return a list of results (WpResults).
        returns empty list on failure.
    """
    if is_empty_query(querystr):
        return []
    # Forces list, and trims queries len > 2
    queries = force_query_list(querystr)
    if not queries:
        # probably had empty or too short queries in the string.
        return []
    
    if not wp_misc.objects.count():
        # Nothing to search
        return []
    
    results = []
    miscobjs = wp_misc.objects.filter(disabled=False)
    for misc in miscobjs.order_by('-publish_date'):
        mcontent = misctools.get_long_desc(misc)
        targets = (misc.name, misc.alias,
                   misc.version, misc.filetype,
                   misc.language, mcontent,
                   misc.description, str(misc.publish_date),
                   )
        got_match = search_targets(queries, targets)
        if got_match:
            goodresult = WpResult(title=misc.name,
                                  desc=highlight_queries(queries,
                                                         misc.description),
                                  link='/misc/#{}'.format(misc.alias),
                                  posted=str(misc.publish_date),
                                  restype='misc')
            results.append(goodresult)
    return results
                
        
def search_projects(querystr):
    """ search all wp_projects and return a list of results (WpResults).
        returns empty list on failure.
    """
    if is_empty_query(querystr):
        return []
    
    queries = force_query_list(querystr)
    if not queries:
        return []
        
    results = []
    if not wp_project.objects.count():
        # Nothing to search
        return []
    projobjs = wp_project.objects.filter(disabled=False)
    for proj in projobjs.order_by('-publish_date'):
        targets = (proj.name, proj.alias,
                   proj.version, proj.description,
                   str(proj.publish_date), ptools.get_html_content(proj),
                   )
        
        got_match = search_targets(queries, targets)
        # Add this project if it matched any of the queries.
        if got_match:
            goodresult = WpResult(title=proj.name + " v." + proj.version,
                                  desc=highlight_queries(queries,
                                                         proj.description),
                                  link='/projects/' + proj.alias,
                                  posted=str(proj.publish_date),
                                  restype='project')
            results.append(goodresult)
    
    return results


def search_targets(queries, targets):
    """ Search all target strings in [targets] for all queries in [queries].
        Returns True on first match, False on no match.
        (no regex used, just 'if s.lower() in t.lower()')
    """
    
    if not queries:
        return False
    
    for target in targets:
        if target:
            target = target.lower()
            for query in queries:
                if query in target:
                    # Return True on first match
                    return True
    return False


def valid_query(querystr):
    """ check for gotchas in search query,
        returns Warning string on failure to pass. """
    
    # Remove double spaces.
    querystr = fix_query_string(querystr)
    
    search_warning = ''
    # Gotcha checkers: 3 character minimum, too many spaces, etc.
    if len(querystr.replace(' ', '')) < 3:
        # check a single term.
        search_warning = "3 character minimum, try again."
    elif ' ' in querystr:
        # check all terms when seperated by a space.
        queries = querystr.split(' ')
        for query_len in [len(q.replace(' ', '')) for q in queries]:
            if query_len == 0:
                search_warning = 'Too many spaces, try again.'
                break
            elif query_len < 3:
                search_warning = ('3 character minimum for all terms, '
                                  'try again.')
                break
    # final illegal char check
    if has_illegal_chars(querystr):
        _log.debug("illegal chars in query: " + querystr)
        search_warning = 'Illegal characters in search term, try again.'

    return search_warning
