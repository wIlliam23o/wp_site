# Django decorators
from django.views.decorators import csrf

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
        if args['partial']:
            kw = {'partial': True}
        else:
            kw = {}
        # Get results.

        try:
            rawresults = lookupfunc(query, **kw)
            results, total = fix_results(rawresults)
        except ValueError as exval:
            errors = exval
        except Exception as ex:
            _log.error('Error looking up number: {}\n{}'.format(query, ex))
            errors = ex

    context = {'request': request,
               'version': app_version,
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


def get_lookup_func(query):
    """ Determines if this is a word or number lookup,
        returns the proper function.
        If no query is given, returns None.
    """
    # Trim some characters from the query.
    query = query.replace('-', '').strip() if query else None

    # If we still have a query, try to get the lookup function.
    if query:
        try:
            # Normal lookup, get phone words.
            intval = int(query)
            query = str(intval)
        except:
            # Reverse lookup, get phone number.
            lookupfunc = phone_words.get_phonenumber
        else:
            # Normal value passed.
            lookupfunc = phone_words.get_phonewords
    else:
        # No query given.
        lookupfunc = None

    return lookupfunc, query
