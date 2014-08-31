#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""phone_words.py
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
VERSION = '1.0.4'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[1]

usage_str = """{verstr}

    Usage:
        {script} <phonenumber> [WORDFILE] [-d] [-p]
        {script} <phonenumber> [WORDFILE] -T [-d] [-p] [-P num]
        {script} <word> -r [-p]
        {script} -g [-s num] [-c cnt] [MAPFILE]
        {script} -t
        {script} -w word [WORDFILE]

    Options:
        <phonenumber>           : Phone number to check.
        <word>                  : Word to find phone number for.
        MAPFILE                 : File name to save pickle data to when
                                  generating a map. Defaults to: phonewords.pkl
        WORDFILE                : File to grab dictionary words from.
                                  Defaults to local words file,
                                  or /usr/share/dict/words.
                                  ...or any file named 'words' in the current
                                     directory.
        -c num,--statcount num  : Number of items to process before printing
                                  the status message. Defaults to: 20
        -d,--debug              : Debug mode, may break normal operation.
        -g,--generatemap        : Generate a map of every possible number
                                  that has a word or words in it.
                                  The data is saved as a pickle.
                                  This is very slow.
        -h,--help               : Show this message.
        -p,--parseable          : Output easy machine-parseable text.
                                  For communicating with a calling process.
                                  Each result is newline separated,
                                  Combo and found word are tab separated,
                                  and only good output will contain a tab.
        -P num,--procs num      : For testing purposes, number of processes
                                  to use when testing with -T.
        -r,--reverse            : Reverse lookup, find number from word.
        -s num,--start num      : Number to start from when generating a map.
        -t,--test               : Run test for known number/words.
        -T,--TEST               : Run basic get_phonewords() with args.
        -v,--version            : Show version.
        -w word,--wordtest word : Test word list to see if it contains a word.

""".format(verstr=VERSIONSTR, script=SCRIPT)
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
    wordfile = argd['WORDFILE'] if argd['WORDFILE'] else get_defaultwordsfile()

    if argd['--generatemap']:
        # Generate the big map of all numbers/words/combos.
        statcnt = force_int((argd['--statcount'] or 20), label='--statcount')
        startnum = force_int((argd['--start'] or 0), label='--start')
        if startnum > 9999999:
            print('That is not a valid starting range: {}'.format(startnum))
            return 1

        mapfile = argd['MAPFILE']
        success = generate_map(
            mapfile,
            wordfile=wordfile,
            start=startnum,
            statuscount=statcnt)

        return 0 if success else 1
    elif argd['--test']:
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
        ret = do_word(argd['<word>'], parseable=argd['--parseable'])
    else:
        # Number lookup.
        ret = do_number(strip_number(argd['<phonenumber>']),
                        wordfile=wordfile,
                        parseable=argd['--parseable'])
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


def do_number(number, wordfile=None, parseable=False):
    """ Run lookup for all combinations of a number. """
    if not check_number(number):
        print('\nInvalid number!'
              '\n    Needs to be 7 or 10 digits long, and no letters.')
        return 1

    numberfmt = format_number(number)
    if not parseable:
        print('Looking up combos for: {}'.format(numberfmt))

    try:
        results, total = get_phonewords(number, wordfile=wordfile)
    except KeyboardInterrupt:
        print('\nUser cancelled.')
        pass
    except Exception as ex:
        if not parseable:
            print('\nError during search:\n{}'.format(ex))
        try:
            if results:
                pass
        except:
            results = None
            total = 0

    if parseable:
        # Machine readable output.
        if results:
            print_parseable(results)
        else:
            print('')
    else:
        # Human readable output.
        if results:
            print('\nFound {} words:'.format(len(results)))
            print_results(results)
        else:
            print('\nNo matches found.')
        if total is not None:
            print('\nTotal attempts: {}'.format(total))

    return 0


def do_word(word, parseable=False):
    """ Run the reverse word lookup. """
    word = word.replace('-', '')
    if not ((len(word) == 7) or (len(word) == 10)):
        if not parseable:
            print('\nThis works better with words that '
                  'are 7 or 10 letters long.')
    if not parseable:
        print('\nLooking up number for: {}'.format(word))

    results = get_phonenumber(word)
    phonenum = results[list(results.keys())[0]]
    if parseable:
        # Machine-readable format.
        print('{}\t{}'.format(word, format_number(phonenum)))
    else:
        # Human-readable format.
        print('\nFound number: {}'.format(format_number(phonenum)))
    return 0


def ensure_nonexisting_filename(filepath):
    """ Ensure a filename that doesn't exist by adding a number to the
        existing filename. (myfile.txt, myfile.2.txt, myfile.3.txt)
    """
    fnum = 2
    dirpath, filename = os.path.split(filepath)
    filestem, fileext = os.path.splitext(filename)
    while os.path.exists(filepath):
        filename = '{name}.{n}{ext}'.format(name=filestem, n=fnum, ext=fileext)
        filepath = os.path.join(dirpath, filename)
        fnum += 1
    return filepath


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


def find_word(number, combos, word):
    """ Searches all combos for a single word (the old fashioned way.)
        Only looks for a single word at a time.
        Used with Pool.map...
    """
    results = {}
    for combo in combos:
        if word in combo:
            fillednum = fill_number(word, combo, number)
            results[fillednum] = word
    # return final results.
    return results


def find_words(number, combos, words):
    """ Find all words in all combos (the old fashioned way.)
        This is for generating the 'big map'.
    """
    results = {}
    for word in words:
        found = find_word(number, combos, word)
        if found:
            if results.get(number, False):
                results[number].update(found)
            else:
                results[number] = found

    return results


def force_int(s, label=None):
    """ Parse a string as an integer, if it fails then exit the program.
        if 'label' is given, a custom error msg is printed.
    """
    try:
        n = int(s)
    except (TypeError, ValueError):
        label = label or ''
        if label:
            label = ' for {}'.format(label)
        print('\nInvalid number{}!: {}'.format(label, s))
        sys.exit(1)
    return n


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


def generate_map(filename=None, wordfile=None, start=2000000, statuscount=10):
    """ Generate the entire map if phone number to words, when given
        a word file to search with.
        This map may be useful for doing a quick number lookup.
        Instead of doing a lettercombo-generate -> word-search every time.
        The phonewords app at welbornprod.com already caches results,
        but since CPython is a lot faster at dictionary lookups than
        my nested for-loops, this may be the better option.

        They will be written as a pickle to the given filename.
        * This will take a long time.
        Arguments:
            filename     : File name to write results to.
                           Default: 'phonewords.pkl'
            wordfile     : File name for words file
                           Default: <the current default word file>
            statuscount  : Number of items to display before showing
                           status.
                           Default: 10 (every ten numbers tried)

    """
    import pickle
    import re
    filename = filename or 'phonewords-{:0>7}.pkl'.format(start)
    # Final results object.
    results = {}
    get_resultlen = results.__len__
    # Patterns that are known to not produce words.
    badpatternstr = (
        '(1|0){5}',  # 5 in a row of 0s or 1s (mixed or same)
        '^(1|0)',  # Starts with 0
        '(1|0){3}[2-9](1|0)',  # 000N0 (mixed 0s and 1s also)
        '(1|0)[2-9](1|0){3}',  # 0N000 (mixed 0s and 1s also)
        '((1|0)[2-9]){3}',  # 0N0N0N (1s also)
        '([2-9](1|0)){3}')  # N0N0N0 (1s also)
    badpatstr = '|'.join(('({})'.format(pat) for pat in badpatternstr))
    badpattern = re.compile(badpatstr)

    # Symbols for bad numbers, none-found numbers, and found numbers.
    # These stream across the console to show progress.
    symbols = {
        #'bad': (color('!', fore='red', style='bold'), 'Impossible number.'),
        'found': (color('.', fore='green'), 'Found words with this number.'),
        'none': (color('x', fore='red'), 'No words found.')
    }
    # Load words.
    wordfile = wordfile or get_defaultwordsfile()
    words = [w for w in iter_filelines(wordfile, maxlength=7)]
    wordlen = len(words)
    wordlenstr = str(wordlen)
    if not words:
        print('\nNo words to use from: {}'.format(wordfile))
        return False
    print('Using {} words from: {}'.format(wordlen, wordfile))

    # Print a symbol by name.
    def printsymbol(name):
        """ Print a status symbol with no newline right away. """
        sys.stdout.write(symbols[name][0])
        sys.stdout.flush()

    print('Legend:')
    for symname, sym in symbols.items():
        print('    {}: {} ({})'.format(symname.rjust(9), sym[0], sym[1]))

    # Start time (for status(), to show time elapsed.)
    starttime = datetime.now()
    # Total number of numbers tried.
    total = 0
    # Total number of 'bad' numbers (impossible to make a word, not tried.)
    totalbad = 0
    # Last good number (number with words)
    lastnumber = None
    # Save the original statuscount so we can reset it later.
    _statuscount = statuscount or 10
    # This is the actual counter for status updates.
    statuscount = _statuscount
    # Calculates elapsed time.
    statustime = lambda: str(datetime.now() - starttime)
    # Transforms a plain status label into a colored/justified label.
    colorlbl = lambda l: color(l.rjust(15), fore='green', style='bold')
    # Format for status updates.
    statuslabels = (
        (colorlbl('Time:'), '{time}'),
        (colorlbl('Total:'), '{total}'),
        (colorlbl('Words:'), '{wordlen}'),
        (colorlbl('Bad:'), '{totalbad}'),
        (colorlbl('Results:'), '{resultlen}'),
        (colorlbl('Number:'), '{number}'),
        (colorlbl('Last Found:'), '{lastnumber}'))
    statusfmt = '\n'.join(('{} {}'.format(l, f) for l, f in statuslabels))

    def status(number):
        """ Show current status. """
        statusargs = {
            'time': color(statustime(), fore='red', style='bold'),
            'total': color(str(total), fore='blue'),
            'totalbad': color(str(totalbad), fore='orange'),
            'resultlen': color(str(get_resultlen()), fore='green'),
            'number': color(number, fore='cyan'),
            'wordlen': color(wordlenstr, fore='blue'),
            'lastnumber': color(lastnumber, fore='yellow'),
        }
        # Print the status message.
        print('\n{}\n'.format(statusfmt.format(**statusargs)))

    try:
        # Python 2.
        ranger = xrange
    except NameError:
        # Python 3.
        ranger = range

    # Flag for when the user cancels (we may be able to pickle half-results)
    cancelled = False
    # Do all possible phone numbers.
    if start < 0:
        start = 0
    for n in ranger(start, 10000000):
        total += 1
        # String for the number, padded with 0's
        number = '{:0>7}'.format(n)
        if badpattern.match(number):
            # printsymbol('bad') # Not printing bad symbols, there's too many.
            totalbad += 1
            continue

        # This number may have words.
        # Create a new generator for the combos.
        combos = get_lettercombos(number)
        if not combos:
            print(color('No combos for: {}'.format(number), fore='red'))
            continue

        try:
            numberresults = find_words(number, combos, words)
        except KeyboardInterrupt:
            print('\nUser cancelled.')
            print('Wasted time: {}'.format(statustime()))
            cancelled = True
            break
        except Exception as ex:
            print('\nError during find_words!: {}'.format(ex))
            break

        if numberresults:
            printsymbol('found')
            results.update(numberresults)
            lastnumber = number
        else:
            printsymbol('none')

        # Time for a status update?
        statuscount -= 1
        if statuscount < 0:
            # Show status stuff.
            status(number)
            # Reset the count.
            statuscount = _statuscount
    else:
        # Made it all the way through.
        print('\n{}\n'.format(color('Success!', fore='green', style='bold')))

    # Print final status.
    status()

    if results:
        # If the starting number is in the filename, add the ending number.
        if str(start) in filename:
            filestem, fileext = os.path.splitext(filename)
            # Add last number to filename.
            filestem = '{}-{}'.format(filestem, number)
            filename = ''.join((filestem, fileext))
        # Make sure the filename doesn't exist already.
        filename = ensure_nonexisting_filename(filename)
        try:
            with open(filename, 'wb') as f:
                pickle.dump(results, f)
        except Exception as ex:
            errfmt = '\nThere was an error writing the pickle!: {}\n{}'
            print(errfmt.format(filename, ex))
            return False
        else:
            # Successful pickle write.
            writemsglbl = color('Results were written to:', fore='green')
            writemsgfile = color(filename, fore='blue', style='bold')
            print(' '.join((writemsglbl, writemsgfile)))
    else:
        print('\n{}'.format(color('No results were found!', fore='red')))
    return True


def get_defaultwordsfile():
    """ Retrieves the default filename for words file. """
    # order of preference for default file.
    if os.path.isfile('words'):
        return 'words'
    elif os.path.isfile('words_trimmed'):
        return 'words_trimmed'
    elif os.path.isfile('/usr/share/dict/words'):
        return '/usr/share/dict/words'
    return None


def get_lettercombos(snumber):
    """ Gets possible letter combinations for a number.
        Does no validation,
        snumber string must contain ONLY number characters.
        No -, or spaces please.
    """
    numberlen = len(snumber)
    words = []
    # Using product() because the positions of the letters matter.
    # This will create every possible letter combination while retaining order.
    # Ex:
    #    numberset = [['a', 'b', 'c'], ['d', 'e', '']]
    #    ..reveals combinations like: 'abc', 'aec', 'dbc', 'dec'
    for combos in itertools.product(*get_letterset(snumber)):
        combostr = ''.join(combos)
        if len(combostr) == numberlen:
            if combostr not in words:
                words.append(combostr)
    return words


def get_letterset(snumber):
    """ Gets possible letter sets for a number.
        No number validation is done,
        the snumber string must contain ONLY number characters.
    """
    return [NUMBERS[n] for n in snumber]


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


def get_phonewords(number, wordfile=None, processes=2):
    """ Same as do_number, but for library use.
        Returns a tuple of: ({letter_combo: word_found}, {stats: value})
        Raises ValueError on invalid number, or empty word list.

        Arguments:
            number        : a phone number to check (string)

        Keyword Arguments:
            wordfile      : Filename to open and get word list from.
                            Default: /usr/share/dict/words
            processes     : Number of processes to use with Pool.map().
                            For testing purposes really.

        Example:
            try:
                foundwords, total = get_phonewords('5555555', myfile)
            except Exception as ex:
                print('Error getting phone words: {}'.format(ex))
            else:
                # Everything went okay, results should be like:
                # foundwords == {'555hand': 'hand'}
                # total == 156789
            * This total is't accurate, it is only an example of what
            * you can find in foundwords and total when get_phonewords returns.
    """

    # Must be valid number.
    if not check_number(number):
        raise ValueError('Invalid number! Needs to be 7 or 10 digits long, '
                         'with no letters.')

    # Get all possible letter combinations for the number.
    combos = [c for c in get_lettercombos(number)]

    # Get word list from file.
    if not wordfile:
        wordfile = get_defaultwordsfile()
        if not wordfile:
            raise ValueError('No default words file available!')

    try:
        # Get word list, which WordFinder will handle.
        wordlist = [w for w in iter_filelines(wordfile, maxlength=len(number))]
    except ValueError:
        raise ValueError('Empty word list given: {}'.format(wordfile))

    # Send to multiprocess pool worker class.
    # Everything up to this point is relatively quick and small.
    # What goes on inside of WordFinder needs to be quick as possible.
    finder = WordFinder(number, combos, wordlist)
    finder.processes = processes

    # Run find_words to compare words/combos.
    # This is where the action is, and where the optimizations are needed.
    foundwords, total = finder.find_words()

    if foundwords:
        # Check for word combinations. (ask9999, 999blah == askblah)
        combined = find_combinedwords(foundwords)
        if combined:
            # Add whole combined words to foundwords.
            foundwords.update({cw: cw for cw in combined})

    return foundwords, total


def iter_filelines(filename, maxlength=10):
    """ Iterates over lines in a word file, does not catch errors.
        For library use.
        Skips lines with ' in them (cannot make a word with ' for this app).
        Yields line.lower() with newlines and quotes stripped.
    """
    maxlen = (maxlength + 1)
    # Change args to test with stackless/pypy
    openargs = {'encoding': 'utf-8'} if sys.version_info.major == 3 else {}
    good_line = lambda l: l and (2 < len(l) < maxlen)
    with open(filename, 'r', **openargs) as fread:
        for line in fread:
            # Strip newlines, then strip "
            line = line.strip('\n').strip('"')
            if good_line(line):
                yield line.lower()
    return


def print_parseable(d):
    """ Print an easy machine-parseable dict. """
    for k in sorted(d.keys()):
        print('{}\t{}'.format(k, d[k]))


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


def test_getphonewords(number, wordfile=None, processes=2):
    """ Run a test of the get_phonewords function. """

    print('\nTesting with: {}'.format(number))
    print('  Procs: {}\n'.format(str(processes)))
    results, total = get_phonewords(number,
                                    wordfile=wordfile,
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
        output = get_phonenumber(testword)[testword]
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


class ColorCodes(object):

    """ This class colorizes text for an ansi terminal.
        Inspired by Colorama (though very different)
    """

    def __init__(self):
        # Linux style color code numbers.
        self.codes = {
            'fore': {
                'black': '30', 'red': '31',
                'green': '32', 'yellow': '33',
                'blue': '34', 'magenta': '35',
                'cyan': '36', 'white': '37',
                'reset': '39'},
            'back': {
                'black': '40', 'red': '41', 'green': '42',
                'yellow': '43', 'blue': '44',
                'magenta': '45', 'cyan': '46', 'white': '47',
                'reset': '49'},
            'style': {
                'bold': '1', 'bright': '1', 'dim': '2',
                'normal': '22', 'none': '22',
                'reset_all': '0',
                'reset': '0'},
        }

        # Format string for full color code.
        self.codeformat = '\033[{}m'
        self.codefmt = lambda s: self.codeformat.format(s)

        # Shortcuts to most used functions.
        self.word = self.colorword

    def color_code(self, fore=None, back=None, style=None):
        """ Return the code for this style/color
            Fixes style positions so a RESET doesn't affect a following color.
        """

        codes = []
        userstyles = {'style': style, 'back': back, 'fore': fore}
        for stype in userstyles:
            style = userstyles[stype].lower() if userstyles[stype] else None
            # Get code number for this style.
            code = self.codes[stype].get(style, None)
            if code:
                # Reset codes come first (or they will override other styles)
                if style in ('none', 'normal', 'reset', 'reset_all'):
                    codes.insert(0, self.codefmt(code))
                else:
                    codes.append(self.codefmt(code))
        return ''.join(codes)

    def colorize(self, text=None, fore=None, back=None, style=None):
        """ Return text colorized.
            fore,back,style  : Name of fore or back color, or style name.
        """
        if text is None:
            text = ''
        return '{codes}{txt}'.format(codes=self.color_code(style=style,
                                                           back=back,
                                                           fore=fore),
                                     txt=text)

    def colorword(self, text=None, fore=None, back=None, style=None):
        """ Same as colorize, but adds a style->reset_all after it. """
        if text is None:
            text = ''
        colorized = self.colorize(text=text, style=style, back=back, fore=fore)
        s = '{colrtxt}{reset}'.format(colrtxt=colorized,
                                      reset=self.color_code(style='reset_all'))
        return s

# Save a global instance of the ColorCodes, and the main function.
colors = ColorCodes()
color = colors.colorword


class WordFinder(object):

    """ Takes every item from one very large list, and searches another large
        list for the existence if list-item1 in list-item2.
        It does this for every item in list1, for every item in list2.

        Basic idea:
            results = {}
            for word in list1:
                for lettercombination in list2:
                    if word in lettercombination:
                        results[lettercombination] = word
            return results

        Actually, right now it uses a Process Pool to help with everything.
    """

    def __init__(self, number, combos, wordlist, processes=None):
        self.number = number or ''
        self.combos = combos or []
        self.combolen = len(self.combos)
        self.wordlist = wordlist or []
        self.wordlen = len(self.wordlist)
        self.chunksize = (self.wordlen // 2) if self.wordlen else 1
        self.totallen = self.combolen * self.wordlen
        self.processes = processes
        self.results = {}

    def find_word(self, word):
        """ Searches all combos for a single word.
            Used with Pool.map...
        """
        # Iterating over self.combos (up to ~5184 items)
        # for every word (up to ~53981 items) for total of
        # ~279,837,504 iterations really sucks.
        # There has to be another way,
        # The requirements are: Check every combo for existence of every word.
        # Words are checked only once, combos are checked for every word.
        for combo in self.combos:
            if word in combo:
                filled = fill_number(word, combo, self.number)
                if filled not in self.results:
                    self.results[filled] = word
                    return self.results
        # no result was found.
        return None

    def find_words(self):
        """ Run all words through find_word using Pool.map """

        if not all((self.number, self.wordlist, self.combos)):
            raise ValueError('Must have a number, a wordlist, and combos!')

        # TODO: Reduce memory footprint and waste on this whole operation.
        def format_results(resultsets):
            """ format final results """
            if resultsets:
                resultsfmt = {}
                for resultset in resultsets:
                    if resultset:
                        resultsfmt.update(resultset)
                return resultsfmt
            return {}

        # setup a pool of processes/workers.
        pool = Pool(processes=self.processes)

        # map find_word to the wordlist, and format final results.
        rawresult = pool.imap(
            self.find_word,
            self.wordlist,
            chunksize=self.chunksize)
        results = format_results(rawresult)

        return results, self.totallen


# MAIN --------------------------
if __name__ == '__main__':
    # Parse args with docopt.
    mainargd = docopt(usage_str, version=VERSIONSTR)

    # Time and run main()
    starttime = datetime.now()
    mainret = main(mainargd)
    duration = round((datetime.now() - starttime).total_seconds(), 3)

    if not mainargd['--parseable']:
        # Print time it took, unless the parseable flag was given.
        print('({} secs.)'.format(str(duration)))

    if mainret is None:
        mainret = 0
    sys.exit(mainret)
