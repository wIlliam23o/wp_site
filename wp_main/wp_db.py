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
    
    decrypted = ''
    if len(skey) > 0:
        tdes = Crypto.Cipher.Blowfish.BlowfishCipher(key=skey)
        decrypted = tdes.decrypt(str_.replace('{nl}', '\n'))
        # trim padding chars.
        while (decrypted.endswith('X')):
            decrypted = decrypted[:-1]
    else:
        decrypted = '[unable to decrypt]'
    return decrypted
        
















