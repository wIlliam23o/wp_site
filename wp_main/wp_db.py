#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - DB Helper
     @summary: Provides various DB/Settings related functions...
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: Apr 28, 2013
'''

import Crypto.Cipher.Blowfish
import os.path
import sys


def get_key(key_filename):
    """ retrieves key from local file """
    skey = '[missing key file]'
    if os.path.isfile(key_filename):
        with open(key_filename) as fread:
            skey = fread.read().strip(' ').strip('\n')
    return skey


def decrypt(skey, str_):
    """ decrypt a string using local key.
        returns empty string on failure.
    """
    
    if isinstance(str_, str) and str_.startswith('b\''):
        str_ = eval(str_)
    decrypted = ''
    if len(skey) > 0:
        tdes = Crypto.Cipher.Blowfish.BlowfishCipher(key=skey)
        # Python 2 has newlines..
        if sys.version < '3':
            str_ = str_.replace('{nl}', '\n')
        decrypted = tdes.decrypt(str_).decode('utf-8')
        # trim padding chars.
        while (decrypted.endswith('X')):
            decrypted = decrypted[:-1]
    else:
        decrypted = '[unable to decrypt]'
    return decrypted
