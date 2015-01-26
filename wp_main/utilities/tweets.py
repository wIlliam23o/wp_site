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
    log = logger('utilities.tweets').log
except ImportError:
    class Log(object):

        def error(self, s):
            print('Error: {}'.format(s))
    log = Log()
    log.error('Django could not be intialized or imported.')
    available = False

try:
    from twython import Twython
except ImportError as eximp:
    log.error('Cannot load Twython! Tweets will not be available.')
    log.error('Twython error was: {}'.format(eximp))
    available = False

SETTINGSFILE = os.path.join(settings.BASE_DIR, 'secret_settings.json')
SETTINGS = {}
if os.path.isfile(SETTINGSFILE):
    try:
        with open(SETTINGSFILE, 'r') as f:
            try:
                SETTINGS = json.loads(f.read())
            except (ValueError) as exjson:
                errmsgfmt = 'Error loading JSON from: {}\n{}'
                log.error(errmsgfmt.format(SETTINGSFILE, exjson))
                available = False
    except EnvironmentError as exread:
        errmsgfmt = 'Error read api key file: {}\n{}'
        log.error(errmsgfmt.format(SETTINGSFILE, exread))
        available = False
else:
    log.error('No api key file found: {}'.format(SETTINGSFILE))
    available = False

if not SETTINGS.get('twitter', {}).get('key', False):
    log.error('Missing api key: twitter.key!')
    available = False
elif not SETTINGS.get('twitter', {}).get('secret', False):
    log.error('Missing api key: twitter.secret!')
    available = False

# Final warning.
if not available:
    log.error('Tweets will not be available!')
# Give the user access to Twython() and the authorization tokens.
twitter = None
auth = None


def get_tweets(screen_name, count=1):
    """ Retrieve latest tweets for a specific screen name. """
    global twitter, auth
    # Don't even bother if the SETTINGS, Django, and everything else is broke.
    if not available:
        log.error('Tweets are not available!')
        return None

    twitterkeys = SETTINGS['twitter']
    if twitter is None:
        try:
            twitter = Twython(twitterkeys['key'], twitterkeys['secret'])
            auth = twitter.get_authentication_tokens()
        except Exception as ex:
            log.error('Error authorizing with twitter:\n{}'.format(ex))
            return {}

    try:
        t = twitter.get_user_timeline(screen_name=screen_name, count=count)
    except Exception as ex:
        errmsgfmt = 'Error getting {} tweets for {}:\n{}'
        log.error(errmsgfmt.format(count, screen_name, ex))
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
