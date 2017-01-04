""" Welborn Productions - Utilities - ID Tools
    Tools that any model can use to generate unique ids.
    These are not safe-guarded ids.
    -Christopher Welborn 2-2-15
"""
from random import SystemRandom

SYSRANDOM = SystemRandom()
# Changing the start char will wreck previously encoded ids.
IDSTARTCHAR = 'a'
# IDPADCHARS cannot contain IDSTARTCHAR + 9 letters (a -> j, when 'a' is used)
IDPADCHARS = 'lmnopqrstuvwxyz'


def encode_id(realid, length=4):
    """ A form of encoding that is reversible.
        Ensures an id at least `length` + `length // 2` characters long.
        Example:
            encode_id(123, length=4)
            'btycydx'

        Arguments:
            realid           : Int or digit string to encode.
            length           : Max length for the actual id.
                               Automatically bumped up to len(str(realid))
                               when needed.
    """
    realidstr = str(realid)
    if not realidstr.isdigit():
        raise ValueError(
            'Expecting a number, or str of digits. Got: ({}) {!r}'.format(
                type(realid).__name__,
                realid,
            )
        )
    realidlen = len(realidstr)
    if realidlen > length:
        # Bump up the length.
        length = realidlen

    startchar = ord(IDSTARTCHAR)
    finalid = []
    for digit in realidstr:
        newchar = chr(startchar + int(digit))
        finalid.append(newchar)

    # Do the actual 'encoding' part.
    while len(finalid) < length:
        finalid.append(SYSRANDOM.choice(IDPADCHARS))

    # Insert random padding characters in random places.
    for _ in range(length // 2):
        finalid.insert(
            SYSRANDOM.randint(0, length - 1),
            SYSRANDOM.choice(IDPADCHARS)
        )
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
