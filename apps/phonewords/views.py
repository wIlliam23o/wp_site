import os.path

# Django decorators
from django.views.decorators import csrf
# Settings
from django.conf import settings

# Local stuff
from wp_main.utilities import responses, utilities
from wp_main.utilities.wp_logging import logger
from apps.phonewords import app_version, phone_words
_log = logger('apps.phonewords').log


@csrf.csrf_protect
def view_index(request):
    """ Main view for phone words. """

    reqargs = responses.get_request_args(request,
                                         requesttype='request',
                                         default='')
    if reqargs:
        # This request came with args, send it to view_results()
        return view_results(request, args=reqargs)
    else:
        # Basic index view.
        context = {'request': request,
                   'version': app_version,
                   'hasargs': False,
                   'extra_style_link_list':
                   [utilities.get_browser_style(request)],
                   }
        return responses.clean_response_req('phonewords/index.html',
                                            context,
                                            request=request)


@csrf.csrf_protect
def view_results(request, args):
    """ Process number/word given by request args. """

    errors = None
    results = None
    total = None
    lookupfunc, query = get_lookup_func(args['query'])
    if lookupfunc:
        # Get wp words file.
        wordfile = os.path.join(settings.BASE_DIR,
                                'apps/phonewords/words')
        if os.path.isfile(wordfile):
            # Get results.
            try:
                rawresults = lookupfunc(query, wordfile=wordfile)
                results, total = fix_results(rawresults)
            except ValueError as exval:
                errors = exval
            except Exception as ex:
                _log.error('Error looking up number: {}\n{}'.format(query, ex))
                errors = ex
        else:
            _log.error('missing word file: {}'.format(wordfile))
            errors = ValueError('Can\'t find word file!')
    # Return response.
    context = {'request': request,
               'version': app_version,
               'hasargs': True,
               'extra_style_link_list':
               [utilities.get_browser_style(request)],
               'query': args['query'],
               'results': results,
               'errors': errors,
               'total': total,
               }

    return responses.clean_response_req('phonewords/index.html',
                                        context,
                                        request=request)


def fix_results(results):
    """ Fixes results from phone_words.get_phonenumber and 
        phone_words.get_phonewords so they return the same types.
    """

    if isinstance(results, dict):
        # Phonenumber results, only returns one thing.
        return results, 1
    elif isinstance(results, (list, tuple)):
        # Phonewords results, ({number: word}, totalcount)
        return results[0], results[1]
    else:
        # Shouldn't get here.
        return results, 0


def get_lookup_cmd(query):
    """ Determines cmdline args needed to run phonewords,
        uses -r if a word was given, and normal if a number was given.
    """

    lookupmethod = get_lookup_method(query)
    argmap = {'word': [query, '-r', '-p'],
              'number': [query, '-p'],
              }
    return argmap.get(lookupmethod, None), query


def get_lookup_func(query):
    """ Determines if this is a word or number lookup,
        returns the proper function.
        If no query is given, returns None.
    """
    lookupmethod = get_lookup_method(query)
    funcmap = {'word': phone_words.get_phonenumber,
               'number': phone_words.get_phonewords,
               }
    return funcmap.get(lookupmethod, None), query


def get_lookup_method(query):
    """ Get lookup args depending query type (number or word)
        Returns 'number', 'word', or None (for bad-query)
    """
    # Trim characters from query.
    if query:
        query = query.replace('-', '').strip()

    querytype = None
    # Still have query after trimming, determine method.
    if query:
        try:
            intval = int(query)
            query = str(intval)
        except ValueError:
            querytype = 'word'
        else:
            querytype = 'number'

    return querytype
