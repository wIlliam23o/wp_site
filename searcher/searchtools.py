#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Welborn Productions - Search - Tools
        Provides various functions for searching welbornproductions

    -Christopher Welborn Mar 28, 2013
'''
import logging
from wp_main.utilities import utilities
from .result import WpResult
log = logging.getLogger('wp.search.tools')

# Apps must have a search.py module that implements these functions:
must_implement = (
    # Desc: Returns full content to search, or None.
    # Signature: get_content(obj, request=None)
    # Ex: get_content = lambda post: post.body
    'get_content',

    # Desc: Returns decription to search and display, or None.
    # Signature: get_desc(obj)
    # Ex: get_desc = lambda post: post.body[:80]
    'get_desc',

    # Desc: Returns searchable objects for the app.
    # Signature: get_objects()
    # Ex: get_objects = lambda : mymodel.objects.filter(disabled=False)
    'get_objects',

    # Desc: Returns target strings to search (built with app.model attrs.)
    # Signature: get_targets(obj, content=None, desc=None)
    # Ex: get_targets = lambda post: (post.title, post.body, post.author)
    'get_targets',

    # TODO: Just have the function return a SearchResult instead.
    # Desc: Returns dict of {
    #       'title': Title for the result (str),
    #       'desc': Description for the result (str),
    #       'link': Relative link for the result (str),
    #       'posted': Published date for the result (str),
    #       'restype': Verbose name for the object (str) (like 'Blog Post')
    #       }
    # Signature: result_args(obj, desc=None)
    'result_args'
)

# Set at end of init. (See bottom.)
SEARCHABLE_APPS = None


def fix_query_string(querystr):
    """ Removes too many spaces from query string. """
    if not hasattr(querystr, 'encode'):
        querystr = str(querystr)

    while '  ' in querystr:
        querystr = querystr.replace('  ', ' ')
    while '++' in querystr:
        querystr = querystr.replace('++', '+')

    return querystr.lower()


def force_query_list(querystr):
    """ If string is passed with ' ', does string.split(),
        if string is passed without ' ', [string] is returned.
        any queries with len(replace(' ', '')) < 3 are culled.
        ...basically forces the use of a list.
    """

    return [q for q in str(querystr).split(' ') if len(q) > 2]


def get_searchable():
    """ Returns only apps that are searchable by the searcher app. """
    return utilities.get_apps(
        include=is_searchable,
        child='search')


def has_illegal_chars(querystr):
    """ check for illegal characters in query,
        returns True on first match, otherwise False.
    """

    illegalchars = (':', '<', '>', ';', 'javascript:', '{', '}', '[', ']')
    for char in illegalchars:
        # log.debug("checking " + char_ + " in " + query_.replace(' ', ''))
        if char in querystr.replace(' ', ''):
            return True

    return False


def is_empty_query(querystring):
    """ returns True if querystring == '', or len(querystring) < 3 """
    if not querystring:
        # Any falsey values are kicked right away (None, False, '')
        return True
    q = str(querystring)
    return (str(q) == '') or (len(q) < 3)


def is_searchable(searchmod):
    """ Checks whether a search.py implements all the must-have functions. """

    # Searching can be disabled simply by putting 'disabled = True' in the
    # module.
    disabled = getattr(searchmod, 'disabled', False)
    if disabled:
        return False

    missing = []
    for funcname in must_implement:
        if not hasattr(searchmod, funcname):
            missing.append(funcname)

    if missing:
        name = getattr(searchmod, '__name__', '<unknown>')
        loglines = [
            'Module {} is missing search functions:'.format(name),
            '    {}'.format('\n    '.join(missing))
        ]
        log.error('\n'.join(loglines))
        return False
    # Module implements all must-have functions.
    return True


def search_all(querystr, request=None):
    """ Searches all searchable apps.
        Arguments:
            querystr       : Query string to search for.
    """
    if is_empty_query(querystr):
        return []

    queries = force_query_list(fix_query_string(querystr))
    if not queries:
        return []

    # TODO: if search_app() returned (relevance_number, item) this could be
    #       ..reworked to sort items based on relevance.
    results = []
    for searchmod in SEARCHABLE_APPS:
        appresults = search_app(searchmod, queries, request=request)
        if appresults:
            results.extend(appresults)

    return results


def search_app(searchmod, queries, request=None):
    """ Search an apps searchable objects and return a list of WpResults.
        Arguments:
            searchmod  : The apps search.py module, imported already.
            queries    : List of string queries to search for.
            request    : Optional Request, if apps need it in search.py.
    """
    results = []
    # TODO: if search_targets() returned a list of matches, then
    #       ..search_app() could return (relevance_numbers, items)
    try:
        for obj in searchmod.get_objects():
            content = searchmod.get_content(obj, request=request)
            desc = searchmod.get_desc(obj)
            targets = searchmod.get_targets(obj, content=content, desc=desc)
            if search_targets(queries, targets):
                resultargs = searchmod.result_args(obj, desc=desc)
                # Not highlighting queries until it can be done right.
                resultargs['desc'] = desc
                results.append(WpResult(**resultargs))
    except Exception as ex:
        logfmt = 'Error searching app: {}\n{}'
        modname = getattr(searchmod, '__name__', '<unknown>')
        log.error(logfmt.format(modname, ex))
    return results


def search_targets(queries, targets):
    """ Search all target strings in [targets] for all queries in [queries].
        Returns True on first match, False on no match.
        (no regex used, just 'if s.lower() in t.lower()')
    """

    # TODO: This could be reworked to show relevance.
    # TODO: The search_all() function could sort items based on relevance.
    if not queries:
        return False

    for target in targets:
        if not target:
            continue
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
    # check all terms when seperated by a space.
    queries = querystr.split(' ')
    for query_len in [len(q.replace(' ', '')) for q in queries]:
        if query_len == 0:
            search_warning = 'Too many spaces, try again.'
            break
        elif query_len < 3:
            search_warning = (
                '3 character minimum for all terms, try again.')
            break
    # final illegal char check
    if has_illegal_chars(querystr):
        log.debug('illegal chars in query: {}'.format(querystr))
        search_warning = 'Weird characters in search term, try again.'

    return search_warning


# Load searchables once.
SEARCHABLE_APPS = get_searchable()
