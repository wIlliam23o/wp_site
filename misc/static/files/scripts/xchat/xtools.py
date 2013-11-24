#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""xtools.py

    Various tools to use with xchat,
    includes /commands that provide specific functionality
    not normally found in xchat/irc, or /commands that enhance the
    xchat experience.

    -Christopher Welborn
"""

from datetime import datetime
import os
import re
import sys

# XChat style version info.
__module_name__ = 'xtools'
__module_version__ = '0.2.3'
__module_description__ = 'Various tools/commands for extending XChat...'
# Convenience version str for help commands.
VERSIONSTR = '{} v. {}'.format(__module_name__, __module_version__)

try:
    # import actual xchat module (from within xchat)
    import xchat
except ImportError:
    print('\nThis cannot be ran outside of XChat!\n')
    sys.exit(1)

# Preload single digit numbers. (for removing leading numbers)
# (remove_leading_numbers())
DIGITS = range(0, 10)
DIGITSTR = [str(i) for i in DIGITS]


def bool_mode(modestr):
    """ Translates common words to bool values.
        Acceptable values for modestr:
            True  : on, true, yes, y, 1 , +,
                    (any number returning True for bool(int(number))
            False : off, false, no, n, 0, -
        Returns True/False per mode.
    """
    # Try int val first
    try:
        intmode = int(modestr)
        return bool(intmode)
    except:
        pass
    # Try string val..
    modestr = modestr.lower()
    if modestr in ('on', 'true', 'yes', 'y', '+'):
        mode = True
    elif modestr in ('off', 'false', 'no', 'n', '-'):
        mode = False
    else:
        invalidmsg = 'Invalid mode for ON/OFF!: {}'.format(modestr)
        print_error(invalidmsg, boldtext=modestr)
        return xchat.EAT_ALL
    return mode


def build_color_table():
    """ Builds a dict of {colorname: colorcode} and returns it. """
    start = ''
    boldcode = ''
    underlinecode = ''
    resetcode = ''

    # Codes (index is the color code)
    codes = ['none', 'black', 'darkblue',
             'darkgreen', 'darkred', 'red', 'darkpurple',
             'brown', 'yellow', 'green', 'darkcyan',
             'cyan', 'blue', 'purple', 'darkgrey', 'grey']

    # Build basic table.
    colors = {}
    for code in range(len(codes)):
        colors[codes[code]] = {'index': code,
                               'code': '{}{}'.format(start, str(code)),
                               }

    # Add style codes.
    # (made up an index for them for now, so color_code(97) will work.)
    colors['bold'] = {'index': 98, 'code': boldcode}
    colors['underline'] = {'index': 97, 'code': underlinecode}
    colors['reset'] = {'index': 99, 'code': resetcode}

    # Add alternate names for codes.
    colors['b'] = colors['bold']
    colors['u'] = colors['underline']
    colors['normal'] = colors['none']
    colors['darkgray'] = colors['darkgrey']
    colors['gray'] = colors['grey']

    return colors


def color_code(color):
    """ Returns a color code by name or mIRC number. """

    try:
        code = COLORS[color]['code']
    except:
        # Try number.
        try:
            codeval = int(color)
            start = ''
            code = '{}{}'.format(start, str(codeval))
        except:
            code = None

    if code:
        return code
    else:
        # Can't find that color! this is the coders fault :(
        print_error('Script error: Invalid color for color_code: '
                    '{}'.format(str(color)),
                    boldtext=str(color))
        return COLORS['reset']['code']


def color_text(color=None, text=None, bold=False, underline=False):
    """ return a color coded word.
        Keyword Arguments:
            color      : Named color, or mIRC color number.
            text       : Text to be colored.
            bold       : Boolean,  whether text is bold or not.
            underline  : Boolean. whether text is underlined or not.
    """

    # normal color code
    boldcode = ''
    underlinecode = ''
    normal = ''
    code = color_code(color)
    # initial text items (basic coloring)
    strcodes = [code, text]
    # Handle extra formatting (bold, underline)
    if underline:
        strcodes.insert(0, underlinecode)
    if bold:
        strcodes.insert(0, boldcode)

    return '{}{}'.format(''.join(strcodes), normal)


def get_all_users(channels=None):
    """ Retrieve a list of all users (no dupes) """

    if not channels:
        channels = xchat.get_list('channels')
    usernames = []
    allusers = []
    for context in [c.context for c in channels]:
        if context:
            users = context.get_list('users')
            for user in users:
                if not user.nick in usernames:
                    allusers.append(user)
                    usernames.append(user.nick)
    return allusers


def get_channel_attrs(attr=None):
    """ Retrieve a channel attribute from all channels.
        ex:
            contexts = get_channel_attrs(attr='context')
    """

    try:
        return [getattr(c, attr) for c in xchat.get_list('channels')]
    except Exception as ex:
        print_error('Error retrieving channel attribute: '
                    '{}'.format(str(attr)),
                    exc=ex,
                    boldtext=str(attr))
        return []


def get_channel_names():
    """ Retrieve all channel names. """

    return [c.channel for c in xchat.get_list('channels')]


def get_channels_users(channels=None):
    """ Return a dict with {channel: [userlist] """
    if not channels:
        channels = xchat.get_list('channels')
    channelusers = {}
    for channel in channels:
        if channel.context:
            users = channel.context.get_list('users')
            channelusers[channel.channel] = users

    return channelusers


def get_cmd_rest(word):
    """ Return the rest of a command. (removing /COMMAND) """

    if word:
        if len(word) == 1:
            return ''
        else:
            rest = word[1:]
            return ' '.join(rest)
    return ''


def get_flag_args(word, arglist):
    """ Retrieves flag args from a command,
        returns a tuple with:
            (cleaned_word, {'--longopt': True/False, ...})
            ...where clean_word has all args removed,
            ...and the dict has long options with True/False value.

        expects:
            word    : from cmd_ word list.
            arglist : list of tuples with [('-s', '--long', False), ...]
                      ('shortoption', 'longoption', default_value)
                      ...default_value is optional and defaults to False.

        Example:
            word = '/cmd -a This is extra stuff.'.split()
            word, argd = get_flag_args(word, [('-a', '--all', False),
                                              ('-c', '--count', True),
                                              ('-d', '--debug', False)])

            Results in:
                word == '/cmd This is extra stuff.'
                argd == {'--all': True,    # the -a flag was used
                         '--count': True,  # it's default is True
                         '--debug': False, # no -d flag was given.
                         }
                * Notice the /cmd is kept, it is useful for certain commands.
                * get_cmd_rest(word) can remove it and return extra stuff only.
    """

    def safe_remove(lst, items):
        """ Safely removes list of items from a lst. """
        for i in items:
            try:
                lst.remove(i)
            except:
                # Item was not in the list.
                pass

    # Build default arg info.
    builtarglist = []
    for argset in arglist:
        if len(argset) < 3:
            shortopt, longopt = argset
            default = False
        elif len(argset) == 3:
            shortopt, longopt, default = argset
        else:
            print('\nInvalid arglist for get_flag_args!: '
                  '{}'.format(repr(argset)))
            return {}
        # Add the proper arg info, for parsing.
        builtarglist.append((shortopt, longopt, default))

    # Parse args, remove them from word as we go.
    newword = [c for c in word]
    arginfo = {}
    for shortarg, longarg, default in builtarglist:
        if (shortarg in word) or (longarg in word):
            # Remove both short and long options from word.
            safe_remove(newword, [shortarg, longarg])
            # Flag was found, set it.
            arginfo[longarg] = True
        else:
            # No short or long, set default.
            arginfo[longarg] = default

    # Return cleaned word, and arg dict.
    return newword, arginfo


def parse_scrollback_line(line):
    """ Parses info out of a xchat scrollback.txt.
        Returns:
            (datetime, nick, msg)
        Or on failure:
            (None, None, None)
    """
    if not line:
        return None, None, None

    lineparts = line.split()
    try:
        # All valid lines consist of: T <timestamp> Nick> Message
        if not line.startswith('T'):
            return None, None, None

        # Parse timestamp.
        timestamp = ' '.join(lineparts[1:2])
        timedate = datetime.fromtimestamp(float(timestamp))

        # Get Message info.
        nickmsg = ' '.join(lineparts[2:])
        if not '>' in nickmsg:
            return None, None, None
        msgparts = nickmsg.split('>')
        nick = msgparts[0].strip('\n').replace(' ', '')
        text = '>'.join(msgparts[1:])
    except (IndexError, ValueError):
        # This was not a channel msg, it was probably plugin output.
        return None, None, None

    if not nick:
        nick = None
    if not text:
        text = None

    return timedate, nick, text


def print_cmdhelp(cmdname=None):
    """ Prints help for a command based on the name.
        If no cmdname is given, all help is shown.
        For /xtools <cmdname>.
        Returns True on success, False on failure (bad cmdname)
    """

    def formathelp(chelpstr):
        """ Color code help string. """
        helplines = chelpstr.split('\n')
        fmthelp = []
        for line in helplines:
            if ':' in line:
                # Color code 'arg : description'
                helpparts = line.split(':')
                argfmt = color_text('blue', helpparts[0])
                descfmt = color_text('darkgrey', helpparts[1])
                line = ':'.join([argfmt, descfmt])
            else:
                # Default color for other lines.
                line = color_text('darkgrey', line)
            # Add indented help line.
            fmthelp.append('    {}'.format(line))
        return '\n'.join(fmthelp)

    def formatcmd(cname):
        """ Format header and help for a command. """
        header = '\nHelp for {}:'.format(cname)
        helpstr = formathelp(cmd_help[cname])
        return '{}\n{}\n'.format(header, helpstr)

    if cmdname:
        # Single command
        cmdname = cmdname.lower().strip('/')
        if cmdname in cmd_help.keys():
            helplist = [formatcmd(cmdname)]
        else:
            print_error('No command named {}'.format(cmdname),
                        boldtext=cmdname)
            return False
    else:
        # All commands.
        helplist = []
        for cmdname in sorted(cmd_help.keys()):
            helplist.append(formatcmd(cmdname))

    # Print the list of help lines.
    print(''.join(helplist))
    return True


def print_cmddesc(cmdname=None):
    """ Prints the description for a command or all commands. """

    # Calculate space needed for formatting, and make a helper function.
    longestname = max([len(k) for k in commands.keys()])
    getspacing = lambda cname: (' ' * (longestname - len(cname) + 4))

    def formatdesc(cname, cdesc):
        """ Format a single description with color codes and spacing. """
        return '{}{} : {}'.format(getspacing(cname),
                                  color_text('blue', cname),
                                  color_text('darkgrey', cdesc))

    if cmdname:
        # Single description, name passed from user.
        cmdname = cmdname.lower().strip('/')
        try:
            cmddesc = commands[cmdname]['desc']
            desclist = [formatdesc(cmdname, cmddesc)]
            print('\nCommand description for {}:'.format(color_text('blue',
                                                                    cmdname)))
        except KeyError:
            print_error('No command named {}'.format(cmdname),
                        boldtext=cmdname)
            return False
    else:
        # All descriptions.
        # Build a list of formatted descriptions for enabled commands.
        desclist = []
        for cname in sorted(commands.keys()):
            if commands[cname]['enabled']:
                desclist.append(formatdesc(cname, commands[cname]['desc']))
        print('\nCommand descriptions for {}:'.format(VERSIONSTR))

    # Print command descriptions.
    print('\n{}\n'.format('\n'.join(desclist)))


def print_colordemo():
    """ A test of color_code and therefor build_color_table also... """

    print('\nTesting colors:\n')
    for cname in sorted(COLORS.keys(), key=lambda k: COLORS[k]['index']):
        cindex = str(COLORS[cname]['index'])
        demotxt = color_text(color=cname, text='{} : {}'.format(cindex, cname))
        print(demotxt)
    print('')


def print_error(msg, exc=None, boldtext=None):
    """ Prints a red formatted error msg.
        Arguments:
            msg       : Normal message to print in red.
            exc       : Exception() object to print (or None)
            boldtext  : Text that should be in Bold (or None)

        Ex:
            print_error('Error in: Main', exc=None, boldtext='Main')
    """

    # Make boldtext bold if it was passed.
    if boldtext:
        # All parts of the message except boldtext.
        msgpart = msg.split(boldtext)
        # Copy of the boldtext, formatted.
        boldfmt = color_text('red', boldtext, bold=True)
        # Formatted normal message parts.
        msgfmt = [color_text('red', s) if s else '' for s in msgpart]
        # Final formatted message.
        msg = boldfmt.join(msgfmt)
    else:
        # Normal message.
        msg = '\n{}\n'.format(color_text('red', msg))

    # Append xtools so you know where this error is coming from.
    msg = '{}{}'.format(color_text('grey', 'xtools: '), msg)
    # Print formatted message.
    print(msg)

    # Print exception.
    if exc:
        print(color_text('red', '\n{}'.format(exc)))


def print_version():
    """ Print xtools version. """

    print(color_text('blue', VERSIONSTR, bold=True))


def remove_leading_numbers(text):
    """ Removes ALL leading numbers, not just single mirc colors. """

    if text:
        while text[0] in DIGITSTR:
            text = text[1:]
    return text


# Helper function for remove_mirc_color (for preloading sub function)
mirc_color_regex = re.escape('\x03') + r'(?:(\d{1,2})(?:,(\d{1,2}))?)?'
mirc_sub_pattern = re.compile(mirc_color_regex).sub


def remove_mirc_color(text, _resubpat=mirc_sub_pattern):
    """ Removes color code from text
        (idea borrowed from nosklos clutterless.py)
        Sub pattern is preloaded on function definition,
        like nosklos (but more readable i think)
    """
    return _resubpat('', text)


def validate_int_str(intstr, minval=5, maxval=60):
    """ Validates a string that is to be converted to an int.
        If minval, maxval is set then ints are auto-rounded to fit
        to the nearest min/max
        Returns: integer on success, None if int(intstr) fails.
    """

    try:
        intval = int(intstr)
    except:
        return None

    if intval < minval:
        intval = minval
    elif intval > maxval:
        intval = maxval

    return intval


# Commands
def cmd_findtext(word, word_eol, userdata=None):
    """ Finds text, and who said it
        Current chat window, or all chat windows.
    """

    # Get current network.
    network = xchat.get_info('network')
    scrollbackbase = os.path.join('~/.xchat2/scrollback', network)
    scrollbackdir = os.path.expanduser(scrollbackbase)
    if not os.path.isdir(scrollbackdir):
        print('Error, no scrollback dir found in: {}'.format(scrollbackdir))
        return xchat.EAT_ALL
    # Get cmd args
    word, argd = get_flag_args(word, [('-a', '--all'),
                                      ('-n', '--nick')])

    # Search query (regex)
    query = get_cmd_rest(word)
    if not query:
        print(cmd_help[word[0].strip('/')])
        return xchat.EAT_ALL

    try:
        querypat = re.compile(query)
    except Exception as exre:
        print_error('\nInvalid search query: {}'.format(query),
                    exc=exre,
                    boldtext=query)
        return xchat.EAT_ALL

    # Get channels pertaining to this search
    if argd['--all']:
        channelnames = get_channel_names()
    else:
        channelnames = [xchat.get_context().get_info('channel')]

    # Search channel data
    print('\n{} {}\n'.format(color_text('blue', 'Searching for:'),
                             color_text('red', query)))
    totalmatches = 0
    for chan in channelnames:
        # Open chan file
        chanfile = os.path.join(scrollbackdir, '{}.txt'.format(chan))
        if os.path.isfile(chanfile):
            try:
                with open(chanfile, 'r') as fread:
                    chandata = fread.readlines()
            except (OSError, IOError) as exio:
                print_error('\nUnable to open: {}'.format(chanfile),
                            exc=exio,
                            boldtext=chanfile)
                chandata = None

        # Search channel lines
        for line in chandata:
            timedate, nick, text = parse_scrollback_line(line)
            # Check parsed output, should always have timedate and nick.
            if None in (timedate, nick):
                continue
            # Nick without colors/codes.
            nickraw = remove_leading_numbers(nick)
            # Check for feedback from server/script output.
            noticemsg = (nickraw == '*')
            if noticemsg or (not text):
                # Skip this line.
                continue
            # Some feedback still passes, check again.
            feedback = nickraw.startswith('[')
            if feedback:
                # Skip this line.
                continue

            # Line passed checks, Match nick..
            rematch = querypat.search(remove_mirc_color(nick))
            if (not rematch) and (not argd['--nick']):
                # Match text if nick_only isn't used.
                rematch = querypat.search(text)

            if rematch and rematch.group():
                totalmatches += 1
                matchtext = rematch.group()
                # Found a match, format it.
                # Get time string. (12-Hour:Minutes:Seconds)
                timestr = timedate.time().strftime('%I:%M:%S')
                # Color code matches.
                text = text.replace(matchtext, color_text(color='red',
                                                          text=matchtext,
                                                          bold=True))
                # Print matches.
                result = '[{}] [{}] {}: {}'.format(color_text('grey', timestr),
                                                   color_text('green', chan),
                                                   color_text('blue', nick),
                                                   text)
                print(result)

    # Finished.
    if totalmatches == 0:
        print(color_text('red', '\nNo matches found.'))
    else:
        print('\nFound {} matches.\n'.format(color_text('blue',
                                                        str(totalmatches))))

    return xchat.EAT_ALL


def cmd_listusers(word, word_eol, userdata=None):
    """ List all users, with a count also. """

    # Get args
    word, argd = get_flag_args(word, [('-a', '--all', False),
                                      ('-c', '--count', False)])

    if argd['--all']:
        print(color_text('blue', '\nGathering users...\n'))
        channels = xchat.get_list('channels')
        userlist = get_all_users(channels=channels)
        userlenstr = str(len(userlist))
        chanlenstr = str(len(channels))
        cntstr = ('\nFound {} users in '.format(color_text(color='blue',
                                                           text=userlenstr)) +
                  '{} channels.\n'.format(color_text(color='blue',
                                                     text=chanlenstr)))
    else:
        userlist = xchat.get_context().get_list('users')
        userlenstr = str(len(userlist))
        cntstr = '\nFound {} users.\n'.format(color_text(color='blue',
                                                         text=userlenstr))
    if argd['--count']:
        # Show count results only.
        print(cntstr)
        return xchat.EAT_ALL

    # List users
    if len(userlist) < 5:
        indention = ''
        joiner = ', '
    else:
        indention = '    '
        joiner = '\n    '

    # Finished
    color_result = lambda u: color_text('blue',
                                        '{} ({})'.format(u.nick,
                                                         u.host))
    userfmt = [color_result(u) for u in userlist]
    print('{}{}'.format(indention, joiner.join(userfmt)))
    print(cntstr)
    return xchat.EAT_ALL


def cmd_searchuser(word, word_eol, userdata=None):
    """ Searches for a user nick,
        expects: word = /searchuser [-a] usernickregex
    """

    if len(word) == 1:
        print(cmd_help['searchuser'])
        return xchat.EAT_ALL

    # Get command args.
    word, argd = get_flag_args(word, [('-h', '--host', False),
                              ('-o', '--onlyhost', False),
        ('-a', '--all', False)])

    match_host = (argd['--host'] or argd['--onlyhost'])

    # All users or current chat?
    channels = xchat.get_list('channels')
    if argd['--all']:
        # All users from every channel.
        print(color_text(color='blue', text='Generating list of all users...'))
        channelusers = get_channels_users(channels=channels)
        userchannels = {}
        allusernames = []
        userlist = []
        for channelname in channelusers.keys():
            for userinf in channelusers[channelname]:
                # Don't add the same name twice.
                # (Apparently 'if userinf in userlist' doesn't work,
                #  Hince the need for 2 lists, one of them only tracking
                #  duplicates.)
                if not userinf.nick in allusernames:
                    userlist.append(userinf)
                    allusernames.append(userinf.nick)

                if userinf.nick in userchannels.keys():
                    # Append channel to this users list
                    # if the channel isn't already there.
                    if not channelname in userchannels[userinf.nick]:
                        userchannels[userinf.nick].append(channelname)
                else:
                    # New channel list for user
                    userchannels[userinf.nick] = [channelname]

    else:
        # Current channel only.
        channelusers = None
        userchannels = None
        userlist = xchat.get_context().get_list('users')

    # Try compiling the query into regex.
    query = get_cmd_rest(word)
    try:
        querypat = re.compile(query)
    except (Exception, re.error) as exre:
        print_error('Invalid query: {}'.format(query),
                    exc=exre,
                    boldtext=query)
        return xchat.EAT_ALL

    # Search
    # Print status (searching for: {})
    print('\n\n{} {} {}'.format(color_text('darkblue', 'xtools'),
                                color_text('blue', 'searching for:'),
                                color_text('red', query)))
    results = []
    for userinf in userlist:
        rematch = None if argd['--onlyhost'] else querypat.search(userinf.nick)
        rehostmatch = querypat.search(userinf.host) if match_host else None

        if rematch:
            results.append(userinf)
        elif rehostmatch:
            results.append(userinf)

    # Print results.
    if results:
        # Setup some default colors (formatting functions)
        colornick = lambda n: color_text(color='blue', text=n)
        colorhost = lambda h: color_text(color='darkpurple', text=h)
        colorchan = lambda cs: color_text(color='darkgreen', text=cs)

        # Sort results for better printing..
        results = sorted(results, key=lambda u: u.nick)

        # Single line results or multi line...
        if len(results) < 5 and (not match_host) and (not argd['--all']):
            # Makes 1 line results.
            indention = ''
            joiner = ', '
        else:
            # List style results.
            indention = '\n    '
            joiner = '\n    '

        # Include host with results string.
        sorted_chans = lambda user: sorted(userchannels[user.nick])
        if match_host:
            # If all_users was used, build a channel list for each nick.
            if argd['-all'] and userchannels:
                newresults = []
                for userinf in [n for n in results]:
                    if userinf.nick in userchannels.keys():

                        newresults.append((userinf.nick,
                                           userinf.host,
                                           ', '.join(sorted_chans(userinf))))
                    else:
                        newresults.append((userinf.nick, userinf.host, ''))
                # Helper function for formatting.
                formatter = lambda t: '{} ({})\n{}{}'.format(colornick(t[0]),
                                                             colorhost(t[1]),
                                                             (' ' * 8),
                                                             colorchan(t[2]))
                # Format the new results.
                resultsfmt = [formatter(i) for i in newresults]
            else:
                # Current channel only, no host.
                formatter = lambda u: '{} ({})'.format(colornick(u.nick),
                                                       colorhost(u.host))
                resultsfmt = [formatter(i) for i in results]

        # Don't include host with results string.
        else:
            # If all_users was used, build a channel list for each nick.
            if argd['--all'] and userchannels:
                newresults = []
                for usernick in [n.nick for n in results]:
                    if usernick in userchannels.keys():
                        newresults.append((usernick,
                                           ', '.join(userchannels[usernick])))
                    else:
                        newresults.append((usernick, ''))
                # Basic format string for user : (channels, channels)
                formatter = lambda t: '{}\n{}{}'.format(colornick(t[0]),
                                                        (' ' * 8),
                                                        colorchan(t[1]))
                # Use the formatter to format results.
                resultsfmt = [formatter(i) for i in newresults]
            else:
                # Show nick only
                resultsfmt = [colornick(n.nick) for n in results]

        formattednicks = '{}{}'.format(indention, joiner.join(resultsfmt))
        # Format footer string.
        if argd['--onlyhost']:
            pluralnicks = 'host' if len(results) == 1 else 'hosts'
        else:
            pluralnicks = 'nick' if len(results) == 1 else 'nicks'
        resultstr = color_text(color='blue', bold=True, text=str(len(results)))
        if argd['--all']:
            chanlenstr = str(len(channels))
            channellenstr = ' in {} channels'.format(color_text('blue',
                                                                chanlenstr))
        else:
            channellenstr = ' in the current channel'
        print('Found {} {}{}: {}\n'.format(resultstr,
                                           pluralnicks,
                                           channellenstr,
                                           formattednicks))
    else:
        print(color_text(color='red', bold=True, text='No nicks found.\n'))

    return xchat.EAT_ALL


def cmd_xtools(word, word_eol, userdata=None):
    """ Shows info about xtools. """

    word, argd = get_flag_args(word, [('-v', '--version', False),
                                      ('-d', '--desc', False),
                                      ('-h', '--help', False),
                                      ('-cd', '--colordemo', False)])
    cmdargs = get_cmd_rest(word)

    # Version only
    if argd['--version']:
        print_version()
        return xchat.EAT_ALL

    # Command description or descriptions.
    if argd['--desc']:
        print_cmddesc(cmdargs)
        return xchat.EAT_ALL

    # Command help.
    if argd['--help']:
        print_cmdhelp(cmdargs)
        return xchat.EAT_ALL

    # Undocumented test for color_code.
    if argd['--colordemo']:
        print_colordemo()
        return xchat.EAT_ALL
    # No args, default behavior
    print_cmddesc(cmdargs)
    return xchat.EAT_ALL


# START OF SCRIPT ------------------------------------------------------------

# List of command names/functions
# (all keys should also be in cmd_help, and vice versa)
commands = {'searchuser': {'desc': 'Find users by name or part of a name.',
                           'func': cmd_searchuser,
                           'enabled': True},
            'finduser': {'desc': '',
                         'func': cmd_searchuser,
                         'enabled': True},
            'findtext': {'desc': 'Search chat text to see who said what.',
                         'func': cmd_findtext,
                         'enabled': True},
            'whosaid': {'desc': '',
                        'func': cmd_findtext,
                        'enabled': True},
            'listusers': {'desc': 'List users in all rooms or current room',
                          'func': cmd_listusers,
                          'enabled': True},
            'xtools': {'desc': 'Show command info or xtools version.',
                       'func': cmd_xtools,
                       'enabled': True},
            }

# Help for commands
cmd_help = {'findtext':
            ('Usage: /FINDTEXT [options]\n'
             'Options:\n'
             '     -a,--all   : Search all open windows.\n'
             '     -n,--nick  : Search nicks only.'),

            'listusers':
            ('Usage: /LISTUSERS [options]\n'
             'Options:\n'
             '    -a,--all    : List from all channels, not just the\n'
             '                  current channel.\n'
             '    -c,--count  : Show count only.'),

            'searchuser':
            ('Usage: /SEARCHUSER [options] <usernick>\n'
             'Options:\n'
             '    <usernick>     : All or part of a user nick to find.\n'
             '                     Regex is allowed.\n'
             '    -a, --all      : Searches all current channels, not\n'
             '                     just the current channel.\n'
             '    -h,--host      : Search host also.\n' +
             '    -o,--onlyhost  : Only search hosts, not nicks.\n'),

            'xtools':
            ('Usage: /XTOOLS [-v] | [[-d | -h] <cmdname>]\n'
             'Options:\n'
             '    <cmdname>               : Show help for a command.\n'
             '                              (same as /help cmdname)\n'
             '    -d [cmd],--desc [cmd]   : Show description for a command,\n'
             '                              or all commands.\n'
             '    -h [cmd],--help [cmd]   : Show help for a command,\n'
             '                              or all commands.\n'
             '     -v,--version           : Show version.\n'
             '\n    * If no options are given, -d is assumed.'),
            }
# Command aliases
# {'aliasname': {'originalcmd': {'helpfix': ('REPLACE', 'REPLACEWITH')}}}
cmd_aliases = {'finduser': {'searchuser': {'helpfix': ('SEARCH', 'FIND')},
                            },
               'whosaid': {'findtext': {'helpfix': ('FINDTEXT', 'WHOSAID')},
                           },
               }
# Fix help and descriptions for aliases
for aliasname in cmd_aliases.keys():
    # Fix help
    for cmd in cmd_aliases[aliasname]:
        replacestr, replacewith = cmd_aliases[aliasname][cmd]['helpfix']
        cmd_help[aliasname] = cmd_help[cmd].replace(replacestr, replacewith)
    # Fix description
    aliasforcmds = list(cmd_aliases[aliasname].keys())
    aliasfor = aliasforcmds[0]
    commands[aliasname]['desc'] = commands[aliasfor]['desc']

# Hook all enabled commands.
for cmdname in commands.keys():
    if commands[cmdname]['enabled']:
        xchat.hook_command(cmdname.upper(),
                           commands[cmdname]['func'],
                           userdata=None,
                           help=cmd_help[cmdname])

# Load Colors
COLORS = build_color_table()

# Load Status Message
print(color_text(color='blue',
                 text='{} loaded.'.format(VERSIONSTR)))
