#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Welborn Productions - Search - Tools
        Provides various functions for searching welbornproductions

    -Christopher Welborn Mar 28, 2013
'''

# Global settings
from django.conf import settings
# For getting searchable apps.
from django.utils.module_loading import import_module
# Safe to view generated html
from django.utils.safestring import mark_safe
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger("search.tools").log

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

    # Desc: Returns target strings to search (built with app.model attributes.)
    # Signature: get_targets(obj, content=None, desc=None)
    # Ex: get_targets = lambda post: (post.title, post.body, post.author)
    'get_targets',

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


class WpResult(object):

    """ holds search result information """

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
        if not restype:
            self.restype = 'Unknown'
        else:
            self.restype = str(restype).title()

    def __str__(self):
        """ String version, for debugging. """
        fmtlines = [
            'WpResult:',
            '  restype: {}',
            '  title  : {}',
            '  link   : {}',
            '  desc   : {}',
            '  posted : {}'
        ]
        return '\n'.join(fmtlines).format(
            self.restype,
            self.title,
            self.link,
            self.description,
            self.posted)

    def __repr__(self):
        """ repr() for debugging. """
        fmt = 'WpResult(\'{t}\', \'{l}\', \'{d}\', \'{p})\', \'{r}\')'
        return fmt.format(
            t=self.title,
            l=self.link,
            d=self.description,
            p=self.posted,
            r=self.restype)


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


def get_apps():
    """ Returns all installed apps modules.
        ...not used right now.
    """
    apps = []
    for appname in settings.INSTALLED_APPS:
        if not appname.startswith('django'):
            try:
                app = import_module(appname)
                apps.append(app)
            except ImportError as ex:
                _log.error('Error importing app: {}\n{}'.format(appname, ex))
    return apps


def get_searchable(apps=None):
    """ Returns only apps that are searchable by the searcher app. """
    searchable = []
    for appname in settings.INSTALLED_APPS:
        if appname.startswith('django'):
            continue
        searchmod = '{}.search'.format(appname)
        try:
            appsearch = import_module(searchmod)
            if is_searchable(appsearch):
                searchable.append(appsearch)
        except ImportError:
            # This app doesn't implement the 'search' module.
            pass

    return searchable


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


def highlight_queries(querystr, scontent):
    """ makes all query words found in the content bold
        by wrapping them in a <strong> tag.
    """

    word_list = scontent.split(' ')
    if isinstance(querystr, (list, tuple)):
        queries = querystr
    else:
        if ',' in querystr:
            querystr = querystr.replace(',', ' ')
        if ' ' in querystr:
            queries = querystr.split(' ')
        else:
            queries = [querystr]
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
        _log.error('\n'.join(loglines))
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

    queries = force_query_list(querystr)
    if not queries:
        return []

    searchmods = get_searchable()
    # TODO: if search_app() returned (relevance_number, item) this could be
    #       ..reworked to sort items based on relevance.
    results = []
    for searchmod in searchmods:
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
                # Highlight queries for the description.
                resultargs['desc'] = highlight_queries(queries, desc)
                results.append(WpResult(**resultargs))
    except Exception as ex:
        logfmt = 'Error searching app: {}\n{}'
        modname = getattr(searchmod, '__name__', '<unknown>')
        _log.error(logfmt.format(modname, ex))
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
