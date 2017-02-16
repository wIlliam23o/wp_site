#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" wppaste.py
    Submit stdin, file content, or single lines to welbornprod.com/paste
    -Christopher Welborn 05-19-2014
"""

import json
import os
import sys
from urllib import request
# from urllib import parse as urlparse

from docopt import docopt
from easysettings import JSONSettings
from http.client import HTTPConnection

settings = JSONSettings.from_file(os.path.join(sys.path[0], 'wppaste.json'))
if not settings.get('author', None):
    settings['author'] = os.environ.get('USER', 'Nobody')
if not settings.get('lang', None):
    settings['lang'] = 'Python'

NAME = 'WpPaste'
VERSION = '1.1.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[-1]

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [options] [TEXT]

    Options:
        TEXT                    : Text to paste.
                                  When no text is given, stdin is used.
                                  If the text is a file name, it will be read
                                  and it's contents will be pasted.
        -a name,--author name   : Set author for the paste.
                                  Defaults to: {author}
        -D,--debug              : Don't paste it, just show the data.
        -h,--help               : Show this help message.
        -H,--hold               : Make this paste on hold.
        -l lang,--lang lang     : Set language for the paste.
                                  Defaults to: {lang}
        -L,--local              : Test local dev paste site.
        -p,--private            : Make this a private paste.
        -r,--raw                : Show raw response from the server.
        -t title,--title title  : Set title for this paste.
                                  Defaults to: (first 32 chars of paste data.)
        -v,--version            : Show version.
        -V,--verbose            : When --debug and --verbose are used,
                                  http client debugging is enabled.
""".format(
    script=SCRIPT,
    versionstr=VERSIONSTR,
    author=settings['author'],
    lang=settings['lang'])

# Default paste domain w/ protocol.
PASTE_DOMAIN = 'https://welbornprod.com'
# Url for json-friendly pastes.
PASTE_URL = '/paste/api/submit'


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    global PASTE_DOMAIN

    if argd['--debug'] and argd['--verbose']:
        HTTPConnection.debuglevel = 1
    if argd['--local']:
        PASTE_DOMAIN = 'http://127.0.0.1'

    pastetxt = argd['TEXT'] or sys.stdin.read()
    # Try reading a file to get the data from.
    if (len(pastetxt) < 256) and os.path.isfile(pastetxt):
        pastetxt = read_file(pastetxt.strip())

    # No empty pastes allowed.
    if not pastetxt.strip():
        print_err('\nNo paste data.\n')
        return 1

    # Build paste data from args, settings, or defaults (in that order).
    title = argd['--title'] or '{}..'.format(pastetxt.strip()[:32])
    author = argd['--author'] or settings['author']
    lang = argd['--lang'] or settings['lang']

    pastedata = {
        'author': author,
        'title': title,
        'content': pastetxt,
        'private': argd['--private'],
        'onhold': argd['--hold'],
        'language': lang,
    }

    if argd['--debug']:
        print('\nPaste Data:\n{}\n'.format(
            json.dumps(pastedata, sort_keys=True, indent=4)))

        if not get_input('Debugging: Continue with paste?'):
            return 0 if save_settings(author, lang) else 1

    # Submit the paste.
    url = pasteit(pastedata, debug=argd['--debug'], raw=argd['--raw'])
    if url is None:
        print_err('\nUnable to submit this paste.')
        return 1
    else:
        print(url)

    # Save settings and exit.
    return 0 if save_settings(author, lang) else 1


def get_input(s):
    """ Return a boolean response from a yes/no question. """
    return input('\n{} (y/n): '.format(s)).strip().lower().startswith('y')


def pasteit(data, debug=False, raw=False):
    """ Submit a paste to welbornprod.com/paste ...
        data should be a dict with at least:
        {'content': <paste content>}

        with optional settings:
        {'author': 'name',
         'title': 'paste title',
         'content': 'this is content',
         'private': True,
         'onhold': True,
         'language': 'Python',
         }
    """
    try:
        newdata = json.dumps(data)
    except Exception as exenc:
        print_err('Unable to encode paste data: {}\n{}'.format(data, exenc))
        return None

    pasteurl = ''.join((PASTE_DOMAIN, PASTE_URL))

    req = request.Request(
        pasteurl,
        data=newdata.encode('utf-8'),
        headers={
            'User-Agent': VERSIONSTR,
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Encoding': 'utf-8'
        })

    try:
        con = request.urlopen(req)
    except Exception as exopen:
        print_err('Unable to open paste url: {}\n{}'.format(pasteurl, exopen))
        return None
    try:
        resp = con.read()
    except Exception as exread:
        print_err('\n'.join((
            'Unable to read paste response from {}:',
            '{}')).format(pasteurl, exread))
        return None
    try:
        resp = resp.decode('utf-8')
        if raw:
            print('\nRaw response:\n{}\n'.format(resp))
        respdata = json.loads(resp)
    except Exception as exjson:
        print_err(
            'Unable to decode JSON from {}\n{}'.format(pasteurl, exjson)
        )
        return None

    status = respdata.get('status', 'error')
    if status == 'error':
        # Server responded with json error response.
        errmsg = respdata.get('message', '<no msg>')
        print_err('Paste site responded with error: {}'.format(errmsg))
        # Paste site errored, no url given to the chat user.
        return None

    # Good response.
    suburl = respdata.get('url', None)
    if suburl:
        finalurl = ''.join((PASTE_DOMAIN, suburl))
        return finalurl

    # No url found to respond with.
    if debug:
        print_err('Server status was okay, but no paste url was given!')
    return None


def print_err(*args, **kwargs):
    """ Wrapper for print that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def read_file(filename):
    """ Read data from a file. Print any errors and return None on failure.
        Return the data on success.
    """
    try:
        with open(filename) as f:
            data = f.read()
    except FileNotFoundError:
        print_err('\nCan\'t find that file!: {}'.format(filename))
        return None
    except EnvironmentError as exio:
        print_err('\nError reading that file: {}\n{}'.format(filename, exio))
        return None

    return data


def save_settings(author, lang):
    settings.update({'author': author, 'lang': lang})
    try:
        settings.save()
    except EnvironmentError as ex:
        print_err('Unable to save settings: {}\n{}'.format(
            settings.filename,
            ex))
        return False
    except ValueError as ex:
        print_err('Error writing JSON settings: {}\n{}'.format(
            settings.filename,
            ex))
        return False
    return True


if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
