""" Welborn Productions - Utilities - ID Tools
    Tools that any model can use to generate unique ids.
    These are not safe-guarded ids.
    -Christopher Welborn 2-2-15
"""
from random import SystemRandom

IDCHOICES = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
SYSRANDOM = SystemRandom()
IDSTARTCHAR = 'a'
IDPADCHARS = ('x', 'y', 'z')


def generate_random_id(length=4):
    """ Generate a random/unique id. """
    finalid = [SYSRANDOM.choice(IDCHOICES) for i in range(length)]
    return ''.join(finalid)


def encode_id(realid):
    """ A form of encoding that is reversible. """
    startchar = ord(IDSTARTCHAR)

    finalid = []
    for c in str(realid):
        newchar = chr(startchar + int(c))
        finalid.append(newchar)
    while len(finalid) < 4:
        finalid.append(SYSRANDOM.choice(IDPADCHARS))
    return ''.join(finalid)


def decode_id(idstr):
    """ Decode an id that has been encoded. """
    startchar = ord(IDSTARTCHAR)
    finalid = []
    for c in idstr:
        if c in IDPADCHARS:
            continue
        intstr = str(ord(c) - startchar)
        finalid.append(intstr)
    return int(''.join(finalid))
