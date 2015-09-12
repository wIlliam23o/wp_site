import logging
import os.path

# Django decorators
from django.views.decorators import csrf
# Settings
from django.conf import settings

# Local stuff
from wp_main.utilities import responses
from apps.phonewords import phone_words, pwtools

from apps.models import wp_app
log = logging.getLogger('wp.apps.phonewords.views')

try:
    phonewordsapp = wp_app.objects.get(alias='phonewords')
    app_version = phonewordsapp.version
except Exception as ex:
    log.error('Phonewords has no database entry!\n'
              'Version will be incorrect:\n{}'.format(ex))
    app_version = '1.0.0'


@csrf.csrf_protect
def view_index(request):
    """ Main view for phone words. """

    reqargs = responses.get_request_args(
        request,
        requesttype='request',
        default='')
    if reqargs:
        # This request came with args, send it to view_results()
        return view_results(request, args=reqargs)
    else:
        # Basic index view.
        context = {
            'version': app_version,
            'hasargs': False,
        }
        return responses.clean_response(
            'phonewords/index.html',
            context=context,
            request=request)


@csrf.csrf_protect
def view_results(request, args=None):
    """ Process number/word given by request args. """

    errors = None
    results = None
    total = None
    rawquery = args['query']
    if not rawquery:
        return responses.error404(request, msgs=['Invalid url args.'])

    lookupfunc, query, method = get_lookup_func(rawquery)
    cache_used = False
    # Try cached results first (for numbers only)
    if method == 'number':
        cachedresult = pwtools.lookup_results(query)
        if cachedresult:
            cache_used = True
            log.debug('Using cached result: {}'.format(cachedresult))
            total = cachedresult.attempts
            results = pwtools.get_results(cachedresult)
            if results:
                # Cancel lookup, we have cached results.
                lookupfunc = None

        else:
            log.debug('No cached found for: {}'.format(query))

    if lookupfunc:
        # Get wp words file.
        wordfile = os.path.join(
            settings.BASE_DIR,
            'apps/phonewords/words')
        if os.path.isfile(wordfile):
            # Get results.
            try:
                rawresults = lookupfunc(query, wordfile=wordfile)
            except ValueError as exval:
                errors = exval
            except Exception as ex:
                log.error('Error looking up number: {}\n{}'.format(query, ex))
                errors = ex
            else:
                # Good results, fix them.
                try:
                    results, total = fix_results(rawresults)
                except Exception as ex:
                    log.error('Error fixing results:\n{}'.format(ex))
                    errmsg = (
                        'Sorry, there was an error parsing the results.<br>{}')
                    errors = Exception(errmsg.format(ex))
                # Cache these results for later if its a number.
                if method == 'number' and (not cache_used):
                    pwtools.save_results(query, results, total)
        else:
            log.error('missing word file: {}'.format(wordfile))
            errors = Exception('Can\'t find word file!')

    # Return response.
    context = {
        'version': app_version,
        'hasargs': True,
        'query': args['query'],
        'results': results,
        'errors': errors,
        'total': total,
    }

    return responses.clean_response(
        'phonewords/index.html',
        context=context,
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

    if query and ('-' in query):
        query = query.replace('-', '')

    lookupmethod = get_lookup_method(query)
    if lookupmethod:
        argmap = {'word': [query, '-r', '-p'],
                  'number': [query, '-p'],
                  }
        return argmap.get(lookupmethod, None), query, lookupmethod
    # no lookup args for that query.
    return None, query, lookupmethod


def get_lookup_func(query):
    """ Determines if this is a word or number lookup,
        returns the proper function.
        If no query is given, returns None.
    """
    if query and ('-' in query):
        query = query.replace('-', '')

    lookupmethod = get_lookup_method(query)
    if lookupmethod:
        funcmap = {'word': phone_words.get_phonenumber,
                   'number': phone_words.get_phonewords,
                   }
        return funcmap.get(lookupmethod, None), query, lookupmethod
    # no lookup method for that query
    return None, query, lookupmethod


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
