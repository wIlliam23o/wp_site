#!/usr/bin/env python3
""" Get latest tweets using Twython.
    This module will fail safely if:
        1) Twython is not installed (not importable)
        2) The API Key can't be found.
        3) There are errors retrieving tweets.
        ...each of these things will be logged, but get_tweets()
           will ultimately return None if these things are not satisfied.
"""
import json
import os
import sys

# This is a module-level flag used to indicate whether or tweets should be
# available to get.
available = True

# Initialize django environment.
try:
    from django.conf import settings
    from wp_main.utilities.wp_logging import logger
    _log = logger('utilities.tweets').log
except ImportError:
    class __log(object):

        def error(self, s):
            print('Error: {}'.format(s))
    _log = __log()
    _log.error('Django could not be intialized or imported.')
    available = False

try:
    from twython import Twython
except ImportError as eximp:
    _log.error('Cannot load Twython! Tweets will not be available.')
    _log.error('Twython error was: {}'.format(eximp))
    available = False

APIKEYFILE = os.path.join(settings.BASE_DIR, 'secretapikeys.json')
APIKEYS = {}
if os.path.isfile(APIKEYFILE):
    try:
        with open(APIKEYFILE, 'r') as f:
            try:
                APIKEYS = json.loads(f.read())
            except (ValueError) as exjson:
                errmsgfmt = 'Error loading JSON from: {}\n{}'
                _log.error(errmsgfmt.format(APIKEYFILE, exjson))
                available = False
    except EnvironmentError as exread:
        errmsgfmt = 'Error read api key file: {}\n{}'
        _log.error(errmsgfmt.format(APIKEYFILE, exread))
        available = False
else:
    _log.error('No api key file found: {}'.format(APIKEYFILE))
    available = False

if not APIKEYS.get('twitter', {}).get('key', False):
    _log.error('Missing api key: twitter.key!')
    available = False
elif not APIKEYS.get('twitter', {}).get('secret', False):
    _log.error('Missing api key: twitter.secret!')
    available = False

# Final warning.
if not available:
    _log.error('Tweets will not be available!')
# Give the user access to Twython() and the authorization tokens.
twitter = None
auth = None


def get_tweets(screen_name, count=1):
    """ Retrieve latest tweets for a specific screen name. """
    global twitter, auth
    # Don't even bother if the APIKEYS, Django, and everything else is broke.
    if not available:
        _log.error('Tweets are not available!')
        return None

    twitterkeys = APIKEYS['twitter']
    if twitter is None:
        try:
            twitter = Twython(twitterkeys['key'], twitterkeys['secret'])
            auth = twitter.get_authentication_tokens()
        except Exception as ex:
            _log.error('Error authorizing with twitter:\n{}'.format(ex))
            return {}

    try:
        t = twitter.get_user_timeline(screen_name=screen_name, count=count)
    except Exception as ex:
        errmsgfmt = 'Error getting {} tweets for {}:\n{}'
        _log.error(errmsgfmt.format(count, screen_name, ex))
        return {}
    return t

if __name__ == '__main__':
    print('\n\nThis module is designed to be used as a library.\n')
    if available:
        print('Latest:\n{}'.format(get_tweets('cjwelborn')))
        sys.exit(0)
    else:
        print('Tweets are not available anyway.')
        sys.exit(1)
