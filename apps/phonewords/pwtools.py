""" Welborn Productions - Apps - PhoneWords - Tools
    Provides various tools for use with PhoneWords.
    -Christopher Welborn
"""

import logging
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from apps.phonewords.models import (
    pw_result,
    InvalidJsonData,
    InvalidJsonObject)  # noqa

log = logging.getLogger('wp.apps.phonewords.tools')


def lookup_results(query):
    """ Looks up a cached result,
        returns the results list if there is one.
        returns None if there isn't one.
    """

    try:
        # lookup a result by query, disabled must be False.
        cachedresult = pw_result.objects.get(query=query, disabled=False)
    except ObjectDoesNotExist:
        # expected for non-cached/disabled results.
        return None
    except MultipleObjectsReturned as exmulti:
        # Should not have duplicate entries
        log.error('Multiple objects found for: {}\n{}'.format(query, exmulti))
        return None
    except Exception as ex:
        # Unexpected error
        log.error('Error looking up cached result: {}\n{}'.format(query, ex))
        return None
    # okay.
    return cachedresult


def get_results(cachedresult):
    """ Decodes the json from a cached result,
        returns an object (dict) on success.
        logs errors and returns None on failure.
    """
    if hasattr(cachedresult, 'query'):
        query = cachedresult.query
    else:
        query = str(cachedresult)

    # decode json.
    try:
        results = cachedresult.get_results()
    except InvalidJsonData as exjson:
        log.error('Cached result had bad json: {}\n{}'.format(query, exjson))
        return None
    except Exception as ex:
        log.error('Error getting results from: {}\n{}'.format(query, ex))
        return None

    return results


def save_results(query, results, attempts):
    """ Create a new pw_result object, save it to the database. """

    try:
        pwresult = pw_result(query=query,
                             result_length=len(results),
                             attempts=attempts)
    except Exception as ex:
        log.error('Can\'t create new result: {}\n{}'.format(query, ex))
        return False

    try:
        pwresult.set_results(results)
    except InvalidJsonObject as exjson:
        log.error('Can\'t set bad json for result: {}\n{}'.format(query,
                                                                  exjson))
        return False
    except Exception as ex:
        log.error('Error saving results for: {}\n{}'.format(query, ex))
        return False

    return True
