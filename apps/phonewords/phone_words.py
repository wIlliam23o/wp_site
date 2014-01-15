#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""phonewords.py
    Finds all possible english words that can be made with a phone number.
    
    -Christopher Welborn 2013
"""

import itertools
import os.path
import sys
from datetime import datetime
from multiprocessing import Pool

from docopt import docopt

NAME = 'PhoneWords'
VERSION = '1.0.2'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)

# Default word list file to use if none was passed.
FILENAME = '/usr/share/dict/words'

usage_str = """phonewords.py

    Usage:
        phonewords.py <phonenumber> [wordfile] [-d] [-p] [-s]
        phonewords.py <phonenumber> [wordfile] -T [-d] [-p] [-P num]
        phonewords.py <word> -r
        phonewords.py -t
        phonewords.py -w word [wordfile]

    Options:
        <phonenumber>           : Phone number to check.
        <word>                  : Word to find phone number for.
        wordfile                : File to grab dictionary words from.
                                  Defaults to {defaultfile}
                                  ...or any file named 'words' in the current
                                     directory.
        -d,--debug              : Debug mode, may break normal operation.
        -h,--help               : Show this message.
        -P num,--procs num      : For testing purposes, number of processes
                                  to use when testing with -T.
        -r,--reverse            : Reverse lookup, find number from word.
        -t,--test               : Run test for known number/words.
        -T,--TEST               : Run basic get_phonewords() with args.
        -v,--version            : Show version.
        -w word,--wordtest word : Test word list to see if it contains a word.

""".format(defaultfile=FILENAME)
# Global flag for debug mode, gets set with '-d' or '--debug' cmdline arg.
DEBUG = False

# Map from number to lettersets.
NUMBERS = {'0': ['0'],
           '1': ['1'],
           '2': ['a', 'b', 'c'],
           '3': ['d', 'e', 'f'],
           '4': ['g', 'h', 'i'],
           '5': ['j', 'k', 'l'],
           '6': ['m', 'n', 'o'],
           '7': ['p', 'q', 'r', 's'],
           '8': ['t', 'u', 'v'],
           '9': ['w', 'x', 'y', 'z'],
           }


# Build map from letter to number.
LETTERS = {}
for numbr in NUMBERS.keys():
    if NUMBERS[numbr]:
        for letr in NUMBERS[numbr]:
            LETTERS[letr] = numbr


def main(argd):
    """ Main entry-point, expects arg dict from docopt. """
    global DEBUG
    DEBUG = argd['--debug']

    reverse_mode = argd['--reverse']
    wordfile = argd['wordfile'] if argd['wordfile'] else FILENAME

    if argd['--test']:
        # Test Run for known matches.
        ret = test_knownwords()
    elif argd['--TEST']:
        # Test get_phonewords()
        procarg = argd['--procs'] if argd['--procs'] else 2
        try:
            procs = int(procarg)
        except:
            print('\nInvalid number for --procs!: {}'.format(procarg))
            return 1
        ret = test_getphonewords(strip_number(argd['<phonenumber>']),
                                 wordfile=wordfile,
                                 processes=procs)
    elif argd['--wordtest']:
        # Test word list for word.
        ret = test_wordlist(wordfile, argd['--wordtest'])
    elif reverse_mode:
        # Word lookup.
        ret = do_word(argd['<word>'])
    else:
        # Number lookup.
        ret = do_number(strip_number(argd['<phonenumber>']), wordfile=wordfile)
    return ret


def add_lists(listoflists):
    """ Given a list of lists, it returns 1 lists with all sub items.
        Works for 2 dimensions only.
    """
    wholelist = []
    for lst in listoflists:
        wholelist.extend(lst)
    return wholelist


def check_number(s):
    """ Checks if a number is valid,
        and is 7 or 10 digits. """
    if '-' in s:
        s = s.replace('-', '')
    s = s.strip()
    # Check for letters
    try:
        intval = int(s)  # noqa
    except:
        # Invalid number.
        return False
    # Return true if the length matches.
    return (len(s) == 7) or (len(s) == 10)


def do_number(number, wordfile=None, partialmatch=False, showall=False):
    """ Run lookup for all combinations of a number. """
    if not check_number(number):
        print('\nInvalid number!'
              '\n    Needs to be 7 or 10 digits long, and no letters.')
        return 1

    numberfmt = format_number(number)
    print('Looking up combos for: {}'.format(numberfmt))
    
    try:
        results, total = get_phonewords(number,
                                        wordfile=wordfile,
                                        partialmatch=partialmatch)
    except KeyboardInterrupt:
        print('\nUser cancelled.')
        pass
    except Exception as ex:
        print('\nError during search:\n{}'.format(ex))
        try:
            if results:
                pass
        except:
            results = None
            total = 0

    if results:
        print('\nFound {} words:'.format(str(len(results))))
        print_results(results)
    else:
        print('\nNo matches found.')
    if total is not None:
        print('\nTotal attempts: {}'.format(str(total)))

    return 0


def do_word(word):
    """ Run the reverse word lookup. """
    word = word.replace('-', '')
    if not ((len(word) == 7) or (len(word) == 10)):
        print('\nThis works better with words that '
              'are 7 or 10 letters long.')
    print('\nLooking up number for: {}'.format(word))

    results = get_phonenumber(word)
    phonenum = results[list(results.keys())[0]]
    print('\nFound number: {}'.format(format_number(phonenum)))
    return 0


def fill_number(word, combo, number):
    """ Fixes junk combos with words in them.
        Returns numbers where junk characters would be,
        to make the word more visible, and cut down on duplicates.
        fill_number('yes', 'XXyesXX', '5550101') == '55yes01'
    """
    start = combo.index(word)
    end = start + len(word)
    if start == 0:
        final = word + number[end:]
    else:
        if end < len(number):
            final = number[:start] + word + number[end:]
        else:
            final = number[:start] + word
    return final


def find_combinedwords(dword):
    """ Searches dict keys (for foundwords), and combines any words
        that can fill the length of the original number.
        Example:
            d = {'5555bag': 'bag', 'fool555': 'fool'}
            combined = find_combinedwords(d)
            if combined:
                print('Found whole words: '.format(' '.join(combined))
            # Combined would return ['foolbag']
    """
    combined = set()
    for actualnum in dword.keys():
        word = dword[actualnum]
        if actualnum.startswith(word):
            restlen = len(actualnum[len(word):])
            for checkagainst in dword.keys():
                endword = dword[checkagainst]
                endstart = checkagainst.index(endword)
                if (len(endword) <= restlen) and (endstart >= len(word)):
                    trimmedend = checkagainst[len(word):]
                    combinedword = '{}{}'.format(word, trimmedend)
                    combined.add(combinedword)
    return list(combined)


def format_number(s):
    """ Formats a phone number like 555-555-5555 or 555-5555.
        If the length is not 7, 10, or 11, it just returns the original input.
    """

    if len(s) == 7:
        return '{}-{}'.format(s[:3], s[3:])
    elif len(s) == 10:
        return '{}-{}-{}'.format(s[:3], s[3:6], s[6:])
    elif len(s) == 11:
        return '{}-{}-{}-{}'.format(s[0], s[1:4], s[4:7], s[7:])
    else:
        return s


def get_defaultwordsfile():
    """ Retrieves the default filename for words file. """
    # Use default file.
    if os.path.isfile('words'):
        return 'words'
    elif os.path.isfile('/usr/share/dict/words'):
        return '/usr/share/dict/words'
    return None


def get_lettercombos(snumber, partialmatch=False, showall=False):
    """ Gets possible letter combinations for a number.
        No -, or spaces please.
    """
    numberlen = len(snumber)
    lettersets = get_letterset(snumber)
    words = set()

    def debugprint(cstr, label=' Letter '):
        if cstr not in words:
            print('{} combo: {}'.format(label, cstr))

    def noprint(*args, **kwargs):
        pass

    printfunc = debugprint if showall else noprint

    for combos in itertools.product(*lettersets):
        combostr = ''.join(combos)
        combolen = len(combostr)
        # easy match, full length combo.
        if combolen == numberlen:
            printfunc(combostr, label=' Letter')
            words.add(combostr)
        elif partialmatch and combolen > 3:
            # Use combos that aren't full length.
            # (slower, but finds more matches)
            combostr = ''
            for i in range(numberlen):
                if combos[i]:
                    combostr += combos[i]
                else:
                    combostr += snumber[i]
            printfunc(combostr, label='Partial')
            words.add(combostr)

    return list(words)


def get_letterset(s):
    """ Gets possible letter sets for a number. """
    sets = []
    for n in s:
        sets.append(NUMBERS[n])
    return sets


def get_phonenumber(word, **kwargs):
    """ Run the reverse word lookup.
        Returns phone number for a given word.
        For library or cmdline use.
        kwargs isn't used.
    """
    numbers = []
    word = word.lower().strip()

    for c in word:
        if c in LETTERS.keys():
            # Convert letter to number.
            numbers.append(LETTERS[c])
        else:
            # Was already a number, just keep it.
            numbers.append(c)
    numberstr = ''.join(numbers)
    return {word: format_number(numberstr)}


#@profile
def get_phonewords(number, wordfile=None, partialmatch=False, processes=2):
    """ Same as do_number, but for library use.
        Returns a tuple of: ({letter_combo: word_found}, {stats: value})
        Raises ValueError on invalid number, or empty word list.

        Arguments:
            number        : a phone number to check (string)

        Keyword Arguments:
            wordfile      : Filename to open and get word list from.
                            Default: /usr/share/dict/words
            partialmatch  : When True, does a deeper search for when words
                            have 0 or 1 in them. It is slower, but produces
                            more results in numbers like that.
                            Default: False
            processes     : Number of processes to use with Pool.map().
                            For testing purposes really.

        Example:
            try:
                foundwords, stats = get_phonewords('5555555', myfile)
            except Exception as ex:
                print('Error getting phone words: {}'.format(ex))
            else:
                # Everything went okay, results should be like:
                # foundwords == {'555hand': 'hand'}
                # stats == {'totalcombos': 5500,
                            'totalsubwords': 13500,
                            'total': 19000,
                            }
            * These results aren't accurate, it is only an example of what
            * you can find in foundwords and stats when get_phonewords returns.
    """

    # Must be valid number.
    if not check_number(number):
        raise ValueError('Invalid number! Needs to be 7 or 10 digits long, '
                         'with no letters.')

    # Get all possible letter combinations for the number.
    combos = [c for c in get_lettercombos(number, partialmatch=partialmatch)]

    # Get word list from file.
    if not wordfile:
        wordfile = get_defaultwordsfile()
        if not wordfile:
            raise ValueError('No default words file available!')

    try:
        # Get generator for word list, which WordFinder will handle.
        wordlist = [w for w in iter_filelines(wordfile, maxlength=len(number))]
    except ValueError:
        raise ValueError('Empty word list given: {}'.format(wordfile))

    # Send to multiprocess pool worker class.
    finder = WordFinder(number, combos, wordlist)
    finder.processes = processes
    foundwords, total = finder.find_words()

    if foundwords:
        # Check for word combinations. (ask9999, 999blah == askblah)
        combined = find_combinedwords(foundwords)
        if combined:
            # Add whole combined words to foundwords.
            foundwords.update({cw: cw for cw in combined})

    return foundwords, total


def iter_filelines(filename, minlength=3, maxlength=10):
    """ Iterates over lines in a word file, does not catch errors.
        For library use.
        Skips lines with ' in them (cannot make a word with ' for this app).
        Yields line.lower() with newlines and quotes stripped.
    """
    # Line is only yielded if it meets this criteria.
    def good_line(l):
        if l:
            llen = len(l)
            if ((llen <= maxlength) and (llen >= minlength) and
               (not "'" in l)):
                return True
        return False
    with open(filename, 'r', encoding='utf-8') as fread:
        for line in fread:
            # Strip newlines, then strip "
            line = line.strip('\n').strip('"')
            if good_line(line):
                yield line.lower()
    return


def iter_listchunk(lst, size=10000):
    """ Iterate over chunks of a list.
        Yields a slice of lst with 'size' as the length.
        Example:
            for items in iter_listchunk(['a', 'b', 'c', 'd'], size=2):
                print(repr(items))
            # prints:
            # ['a', 'b']
            # ['c', 'd']
    """

    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def print_results(d, spacelen=None):
    """ Prints a dict, sorted by key.
        Keyword Arguments:
            spacelen  : Number of spaces for indention.
                        Default: None
    """
    indention = (' ' * spacelen) if spacelen else ''
    for k in sorted(d.keys()):
        print('{}{}: {}'.format(indention, k, str(d[k])))


def strip_number(s):
    """ Strips all spaces and - from a number. """

    if '-' in s:
        s = s.replace('-', '')
    return s.strip()


def test_getphonewords(number, wordfile=None, partialmatch=False, processes=2):
    """ Run a test of the get_phonewords function """

    print('\nTesting with: {}'.format(number))
    print('Partial: {}'.format(str(partialmatch)))
    print('  Procs: {}\n'.format(str(processes)))
    results, total = get_phonewords(number,
                                    wordfile=wordfile,
                                    partialmatch=partialmatch,
                                    processes=processes)
    if results:
        print('\nFound {} matches:'.format(str(len(results))))
        print_results(results)
        ret = 0
    else:
        print('\nNo matches.')
        ret = 1
    print('\nTotal attempts: {}'.format(str(total)))
    return ret


def test_knownwords():
    """ Just a test to see if known number/word matches are found. """
    expected = {'3643663': 'dogfood',
                '2284264': 'cathang',
                '3665224': 'foolbag',
                }
    # Build result dict, will be changed during tests.
    results = {k: [] for k in expected.keys()}
    failures = 0
    total = 0
    # Do number test.
    for testnum in expected.keys():
        total += 1
        expectedword = expected[testnum]
        output = get_lettercombos(testnum)
        if expectedword in output:
            results[testnum].append('Number Pass: '
                                    '{} (found)'.format(expectedword))
        else:
            results[testnum].append('Number Failed for: '
                                    '{} (not found)'.format(expectedword))
            failures += 1

    # Do word test.
    for testnum, testword in expected.items():
        total += 1
        output = get_phonenumber(testword)
        if strip_number(output) == testnum:
            results[testnum].append('Word Pass: {}'.format(output))
        else:
            results[testnum].append('Word Failed for: '
                                    '{} (got {})'.format(testnum, output))
            failures += 1

    # Print results...
    for resultnum, resultlst in results.items():
        spacing = (' ' * len(resultnum))
        print('{}:'.format(resultnum))
        print('{}{}'.format(spacing,
                            '\n{}'.format(spacing).join(resultlst)))

    totalstr = str(total)
    failuresstr = str(failures)
    successstr = str(total - failures)
    print('Ran {} tests. {} passed, {} failed.'.format(totalstr,
                                                       successstr,
                                                       failuresstr))
    return 1 if failures else 0


def test_wordlist(filename, word):
    """ Check if a word is in the word list for testing. """

    linegen = iter_filelines(filename, maxlength=len(word))
    word = word.lower().strip()
    print('\nChecking for {} in {}:'.format(word, filename))
    foundwords = []
    try:
        for line in linegen:
            if word == line:
                print('    Found whole match: {}'.format(line))
                foundwords.append(word)
            elif line in word:
                print('    Found part match : {}'.format(line))
                foundwords.append(word)
    except Exception as ex:
        print('\nError checking word list:\n{}'.format(ex))
        pass
    print('\nFound {} words in {}'.format(str(len(foundwords)), filename))
    return 0 if foundwords else 1


class WordFinder(object):

    """ Finds all possible letter combinations for a phone number,
        searches a word list for matches.
    """

    def __init__(self, number, combos, wordlist, processes=2):
        self.number = number
        self.combos = combos
        self.wordlist = wordlist
        self.processes = processes

    def find_word(self, word):
        """ Searches all combos for a single word.
            Used with Pool.map...
        """

        results = {}
        for combo in self.combos:
            if word in combo:
                filled = fill_number(word, combo, self.number)
                if filled not in results.keys():
                    results[filled] = word
        return results

    def find_words(self):
        """ Run all words through find_word using Pool.map """

        # TODO: make WordFinder take in a generator,
        #       then feed small blocks from that generator to pool.map
        #       so pool.map is happy with getting a full list(), and
        #       the memory won't be so heavy.
        #       loop over the block updating results as the map functions
        #       finish.
        #       If I could do something like that for self.combos also
        #       that would be great. Although the wordlist outweighs the
        #       combos by far. It should be split into chunks at least.
        resultsfmt = {}
        pool = Pool(processes=self.processes)
        for wordset in iter_listchunk(self.wordlist):
            resultsets = pool.map(self.find_word, wordset)
            # Update all results with this set of results.
            for resultset in resultsets:
                if resultset:
                    resultsfmt.update(resultset)

        return resultsfmt, (len(self.wordlist) * len(self.combos))


# MAIN --------------------------
if __name__ == '__main__':
    mainargd = docopt(usage_str, version=VERSIONSTR)
    starttime = datetime.now()
    mainret = main(mainargd)
    duration = round((datetime.now() - starttime).total_seconds(), 3)
    print('({} secs.)'.format(str(duration)))
    if mainret is None:
        mainret = 0
    sys.exit(mainret)
