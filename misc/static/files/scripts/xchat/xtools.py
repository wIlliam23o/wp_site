#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""xtools.py

    Various tools to use with xchat,
    includes /commands that provide specific functionality
    not normally found in xchat/irc, or /commands that enhance the
    xchat experience.

    This script is now over 2000+ lines, and I really wish it weren't so.
    It's time to shut this little project down before it requires a
    RAM upgrade. I really wanted this to be a single script project, but
    things like cmd_help, and non-xchat functions really need their own home.

    -Christopher Welborn
"""

from code import InteractiveInterpreter
from collections import deque
from datetime import datetime
import os
import re
import sys
from threading import Thread
# XChat style version info.
__module_name__ = 'xtools'
__module_version__ = '0.3.2'
__module_description__ = 'Various tools/commands for extending XChat...'
# really minor changes bump this 'versionx'
VERSIONX = '1'
# Convenience version str for help commands.
VERSIONSTR = '{} v. {}-{}'.format(__module_name__,
                                  __module_version__,
                                  VERSIONX)

try:
    # import actual xchat module (from within xchat)
    import xchat
except ImportError:
    print('\nThis cannot be used outside of XChat!\n')
    sys.exit(1)

# TODO: Remove dead (commented-code here, and remove_leading_numbers)
# Preload single digit numbers. (for removing leading numbers)
# (remove_leading_numbers(), is called on every filtered msg.)
#DIGITS = range(0, 10)
#DIGITSTR = [str(i) for i in DIGITS]

# Default config file.
XCHAT_DIR = os.path.expanduser('~/.xchat2')
if os.path.isdir(XCHAT_DIR):
    CONFIG_FILE = os.path.join(XCHAT_DIR, 'xtools.conf')
else:
    # Can't find xchat dir, just use CWD.
    CONFIG_FILE = os.path.join(os.getcwd(), 'xtools.conf')

# Dict to hold settings. (loaded from preferences if available)
SETTINGS = {}
# Dict of ignored nicks. (loaded from preferences if available)
# Contains nicks as keys, {'index': ?, 'pattern', ?} as values.
# Index is the alphabetically sorted index, pattern is a compiled regex pattern
# {'nick2': {'index': 1, 'pattern': <SRE_Pattern>},
#  'nick1': {'index': 0, 'pattern': <SRE_Pattern>}}
IGNORED_NICKS = {}
MAX_IGNORED_MSGS = 250
# Deque of ignored messages, only for this session. Max length is set.
IGNORED_MSGS = deque(maxlen=MAX_IGNORED_MSGS)

# Dict of msg catchers (regex/text to catch and save msgs)
MSG_CATCHERS = {}
# Deque of caught messages, only for this session.
MAX_CAUGHT_MSGS = 250
CAUGHT_MSGS = {}

# Title for the xtools tab/window..
XTOOLS_TAB_TITLE = '[xtools]'


class StdOutCatcher(object):

    """ Context that catches stdout for code inside the 'with' block.


        Usage:
            with StdOutCatcher(safe=True, maxlength=160) as fakestdout:
                # stdout is stored in fakestdout.output
                print('okay')
            # stdout is back to normal
            # retrieve the captured output..
            print('output was: {}'.format(fakestdout.output))
    """

    def __init__(self, safe=True, maxlength=160):
        # Use safe_output?
        self.safe = safe
        # Maximum length before trimming output
        self.maxlength = maxlength
        # Output
        self.outlines = []
        self.output = ''

    def __enter__(self):
        # Replace stdout with self, stdout.write() will be self.write()
        self.oldstdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, type, value, traceback):
        # Fix stdout.
        sys.stdout = self.oldstdout

    def safe_output(self, s):
        """ Make output safe for chat (no newlines, length trimmed) """

        s = s.replace('\n', '\\n')
        if (self.maxlength > 0) and (len(s) > self.maxlength):
            s = '{} (..truncated)'.format(s[:self.maxlength])
        return s

    def write(self, s):
        s = s.strip('\n')
        if s:
            # Use chat-safe output.
            if self.safe:
                s = self.safe_output(s)
            # Save output
            self.outlines.append(s)
            self.output = '\\n'.join(self.outlines)


class StdErrCatcher(StdOutCatcher):

    """ Same as StdOutCatcher, but works with stderr instead. """

    def __enter__(self):
        self.oldstderr = sys.stderr
        sys.stderr = self
        return self

    def __exit__(self, type, value, traceback):
        sys.stderr = self.oldstderr


class TabWaiter(object):

    """ Waits for a user-defined amount of time for
        a certain tab to become focused.
        Use with caution!
    """

    def __init__(self, tabtitle=None, timeout=5):
        self.tabtitle = tabtitle if tabtitle else XTOOLS_TAB_TITLE
        self.timeout = timeout
        self._context = None

    def check_tab(self):
        """ This must run in a seperate thread, or xchat will lock up. """
        foundtab = xchat.find_context(channel=self.tabtitle)
        while not foundtab:
            foundtab = xchat.find_context(channel=self.tabtitle)
        # set result.
        self._context = foundtab

    def ensure_tab(self):
        """ ensure that this tab is opened.
            times out after self.timeout seconds.
            returns the tab's context on success, or None on timeout.
        """
        tabcontext = xchat.find_context(channel=self.tabtitle)
        if tabcontext:
            # tab already opened
            return tabcontext
        # open and wait for tab.
        self.open_tab()
        return self.wait_for_tab()

    def open_tab(self):
        xchat.command('QUERY {}'.format(self.tabtitle))

    def wait_for_tab(self):
        finder = Thread(target=self.check_tab, name='TabWaiter')
        finder.start()
        finder.join(timeout=self.timeout)
        return self._context


def add_ignored_nick(nickstr):
    """ Add a nick to the ignored list. """
    global IGNORED_NICKS
    ignored_nicks = []

    if ((nickstr.startswith('"') and nickstr.endswith('"')) or
       (nickstr.endswith("'") and nickstr.endswith("'"))):
        # quoted spaces..
        nicks = nickstr[1:-1]
    else:
        # This will accept several nicks separated by spaces.
        nicks = nickstr.split()
    
    for nick in nicks:
        if nick in IGNORED_NICKS.keys():
            # Skip nick already on the list.
            print_status('{} is already ignored.'.format(nick))
            continue
        repat, reerr = compile_re(nick)
        if not repat:
            # Skip bad regex.
            print_error('Invalid regex pattern for that nick: {}'.format(nick),
                        boldtext=nick,
                        exc=reerr)
            continue
        IGNORED_NICKS[nick] = {'index': len(IGNORED_NICKS),
                               'pattern': repat,
                               }

        ignored_nicks.append(nick)

    # Fix indexes so they are sorted.
    build_ignored_indexes()
    if ignored_nicks and save_ignored_nicks() and save_prefs():
        
        return ignored_nicks
    # Failure saving.
    return []


def add_catcher(catcherstr):
    """ Add a catcher to the catchers list. """
    global MSG_CATCHERS
    msg_catchers = []

    if ((catcherstr.startswith('"') and catcherstr.endswith('"')) or
       (catcherstr.endswith("'") and catcherstr.endswith("'"))):
        # quoted spaces...
        catchers = catcherstr[1:-1]
    else:
        # This will accept several catchers separated by spaces.
        catchers = catcherstr.split()
    for msg in catchers:
        if msg in MSG_CATCHERS.keys():
            # Skip nick already on the list.
            print_status('{} is already caught.'.format(msg))
            continue
        repat, reerr = compile_re(msg)
        if not repat:
            # Skip bad regex.
            print_error(('Invalid regex pattern for that catcher: '
                        '{}'.format(msg)),
                        boldtext=msg,
                        exc=reerr)
            continue
        MSG_CATCHERS[msg] = {'index': len(MSG_CATCHERS),
                             'pattern': repat,
                             }

        msg_catchers.append(msg)

    # Fix indexes so they are sorted.
    build_catcher_indexes()
    if msg_catchers and save_catchers() and save_prefs():
        return msg_catchers
    # Failure saving.
    print_error('Unable to save catchers...')
    return []


def add_caught_msg(msginfo):
    """ add a message to the caught-msgs dict, if it doesn't exist. """
    global CAUGHT_MSGS
    # Caught messages need to have a unique id for each caught msg,
    # or else it will cause double msgs, or recursion in some cases.
    # hince the need for add_caught_msg(), which generates and checks
    # duplicate msg ids.

    msgid = generate_msg_id(msginfo)
    existingmsg = CAUGHT_MSGS.get(msgid, None)
    if existingmsg:
        return False

    # This would be really slow, if the msg len has exceeded the max and
    # a lot of msgs are being added.
    if len(CAUGHT_MSGS) >= MAX_CAUGHT_MSGS:
        # pop the first item from caught msgs.
        sortbytime = lambda msgid: CAUGHT_MSGS[msgid]['time']
        firstkey = list(sorted(CAUGHT_MSGS.keys(), key=sortbytime))[0]
        CAUGHT_MSGS.pop(firstkey)
    CAUGHT_MSGS[msgid] = msginfo
    return True


def add_message(addfunc, nick, msgtext, msgtype=None):
    """ Uses the given 'add function' to add a filtered/saved msg.
        This builds a universal message format that should be used
        anywhere a message is saved.
        ex:
            add_message(IGNORED_MSGS.append, 'user1', 'my message')
            # or
            add_message(add_caught_msg, 'user2', 'my msg')
        .. will use IGNORED_MSGS.append, or add_caught_msg to save the message.
        The function has to receive a single argument, which is a msg in the
        universal format.
    """
    chan = xchat.get_context().get_info('channel')
    msgtime = datetime.now()
    if msgtype:
        # set message type (channelmessage, channelaction, etc.)
        msgtype = msgtype.lower().replace(' ', '')
    else:
        # no message type set.
        msgtype = ''
    msg = {'nick': nick,
           'time': msgtime.time().strftime('%H:%M:%S'),
           'date': msgtime.date().strftime('%m-%d-%Y'),
           'channel': chan,
           'type': msgtype,
           'msg': msgtext}
    try:
        addfunc(msg)
        return True
    except Exception as ex:
        if hasattr(addfunc, '__name__'):
            addfuncname = addfunc.__name__
        else:
            addfuncname = repr(addfunc)
        print_error('Error adding saved msg with: {}'.format(addfuncname),
                    exc=ex,
                    boldtext=addfuncname)
        return False


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


def build_catcher_indexes():
    """ Builds indexes for msg catchers. """
    global MSG_CATCHERS
    for index, msg in enumerate(sorted(MSG_CATCHERS.keys())):
        MSG_CATCHERS[msg]['index'] = index


def build_ignored_indexes():
    """ Builds indexes for ignored nicks. """
    global IGNORED_NICKS
    for index, nick in enumerate(sorted(IGNORED_NICKS.keys())):
        IGNORED_NICKS[nick]['index'] = index


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
    for i, code in enumerate(codes):
        colors[code] = {'index': i,
                        'code': '{}{}'.format(start, str(i)),
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


def clear_catchers():
    """ Clears all catchers """
    global MSG_CATCHERS

    if not MSG_CATCHERS:
        print_error('The catch-msg list is already empty.')
        return False

    MSG_CATCHERS = {}
    if save_catchers() and save_prefs():
        return True
    return False


def clear_caught_msgs():
    """ Clears all caught msgs. """
    global CAUGHT_MSGS

    if not CAUGHT_MSGS:
        print_error('No messages have been caught.')
        return False

    CAUGHT_MSGS = {}
    return True


def clear_ignored_nicks():
    """ Clears all ignored nicks. """
    global IGNORED_NICKS

    if not IGNORED_NICKS:
        print_error('The ignore list is already empty.')
        return False

    IGNORED_NICKS = {}
    if save_ignored_nicks() and save_prefs():
        return True
    return False


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


def compile_re(restr):
    """ Try compiling a regex, returns (repat, exception)
        so it fails, it returns (None, exception)
        if it succeeds, it returns (repat, None)
    """
    try:
        compiled = re.compile(restr)
    except Exception as ex:
        return False, ex
    else:
        return compiled, None


def generate_msg_id(msginfo):
    """ Generate a unique msg id for caught msgs. """

    chan = xchat.strip(msginfo['channel'])
    nick = xchat.strip(msginfo['nick'])
    msg = xchat.strip(msginfo['msg'])

    return hash('{}{}{}'.format(chan, nick, msg))


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
    arginfo = {}
    for argset in arglist:
        if len(argset) < 3:
            shortopt, longopt = argset
            arginfo[longopt] = False
        elif len(argset) == 3:
            shortopt, longopt, default = argset
            arginfo[longopt] = default
        else:
            print('\nInvalid arglist for get_flag_args!: '
                  '{}'.format(repr(argset)))
            return {}
        # Add the proper arg info, for parsing.
        builtarglist.append((shortopt, longopt))

    # Parse args, remove them from word as we go.
    newword = [c for c in word]
    for shortarg, longarg in builtarglist:
        if (shortarg in word) or (longarg in word):
            # Remove both short and long options from word.
            safe_remove(newword, [shortarg, longarg])
            # Flag was found, set it.
            arginfo[longarg] = True

    # Return cleaned word, and arg dict.
    return newword, arginfo


def get_pref(opt):
    """ Retrieve a preference from settings.
        Returns None if it's not available.
    """

    if opt in SETTINGS.keys():
        return SETTINGS[opt]
    return None


def get_xtools_window():
    """ Open the xtools tab, and wait for it to be focused.
        Returns the xtools-tab context (unless it times out, then None)
    """

    tabwaiter = TabWaiter(tabtitle=XTOOLS_TAB_TITLE)
    xchatwin = tabwaiter.ensure_tab()
    return xchatwin


def load_catchers():
    """ Loads msg-catchers from preferences. """
    global MSG_CATCHERS

    catcher_str = get_pref('msg_catchers')
    if catcher_str:
        catchers = [s.strip() for s in catcher_str.split('{|}')]
    else:
        catchers = []

    # Validate nicks.
    valid = {}
    for msg in catchers:
        repat, reerr = compile_re(msg)
        if reerr:
            print_error('Invalid regex pattern for msg-catcher in config: '
                        '{}'.format(msg),
                        boldtext=msg,
                        exc=reerr)
            continue
        # Have good nick pattern, add it.
        valid[msg] = {'index': len(valid), 'pattern': repat}

    # Save to global.
    MSG_CATCHERS.update(valid)
    # Rebuild indexes
    build_catcher_indexes()
    return True


def load_ignored_nicks():
    """ Loads ignored nicks from preferences. """
    global IGNORED_NICKS

    ignored_str = get_pref('ignored_nicks')
    if ignored_str:
        if ',' in ignored_str:
            ignored = [s.strip() for s in ignored_str.split(',')]
        else:
            ignored = [ignored_str.strip()]
    else:
        ignored = []

    # Validate nicks.
    valid = {}
    for nick in ignored:
        repat, reerr = compile_re(nick)
        if reerr:
            print_error('Invalid regex pattern for nick in config: '
                        '{}'.format(nick),
                        boldtext=nick,
                        exc=reerr)
            continue
        # Have good nick pattern, add it.
        valid[nick] = {'index': len(valid), 'pattern': repat}

    # Save to global.
    IGNORED_NICKS.update(valid)
    # Rebuild indexes
    build_ignored_indexes()
    return True


def load_prefs():
    """ Load all preferences (if available). """
    global SETTINGS

    try:
        with open(CONFIG_FILE, 'r') as fread:
            configlines = fread.readlines()
    except (IOError, OSError) as exio:
        if not os.path.isfile(CONFIG_FILE):
            return False
        # Actual error, alert the user.
        print_error('Can\'t open config file: {}'.format(CONFIG_FILE),
                    boldtext=CONFIG_FILE,
                    exc=exio)
        return False

    # Have config lines.
    for line in configlines:
        line = line.strip('\n').strip()
        if line.startswith('#') or (line.count('=') != 1):
            # Skip comment/bad config line.
            continue
        # Have good config line.
        opt, val = [s.strip() for s in line.split('=')]
        SETTINGS[opt] = val
    return True


def longest(lst):
    return len(max(lst, key=len))


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


def print_catchers():
    """ Prints all msg catchers. """

    if not MSG_CATCHERS:
        print_status('No msg catchers have been set.')
        return True

    catchlen = str(len(MSG_CATCHERS))
    caughtlen = str(len(CAUGHT_MSGS))
    statusmsg = ('Message Catchers ({} catchers - {} caught msgs):'.format(
        color_text('blue', catchlen),
        color_text('blue', caughtlen))
    )
    print_status(statusmsg)
    msgsortkey = lambda k: MSG_CATCHERS[k]['index']
    for msg in sorted(MSG_CATCHERS.keys(), key=msgsortkey):
        istr = str(MSG_CATCHERS[msg]['index'] + 1)
        line = '    {}: {}'.format(color_text('blue', istr, bold=True),
                                   color_text('blue', msg))
        print(line)
    return True


def print_caught_msgs():
    """ Prints all caught messages for this session. """

    if CAUGHT_MSGS:
        # Print ignored messages.
        msglen = len(CAUGHT_MSGS)
        msglenstr = color_text('blue', str(msglen), bold=True)
        msgplural = 'message' if msglen == 1 else 'messages'
        chanspace = longest([CAUGHT_MSGS[m]['channel'] for m in CAUGHT_MSGS])
        nickspace = longest([CAUGHT_MSGS[m]['nick'] for m in CAUGHT_MSGS])

        print_status('You have {} caught {}:\n'.format(msglenstr, msgplural))
        sortkey = lambda k: CAUGHT_MSGS[k]['time']
        for msgid in sorted(CAUGHT_MSGS, key=sortkey):
            print_saved_msg(CAUGHT_MSGS[msgid],
                            chanspace=chanspace,
                            nickspace=nickspace)
        return True
    else:
        # print 'no messages' warning.
        catchlen = len(MSG_CATCHERS)
        catchlenstr = color_text('blue', str(catchlen))
        catchplural = 'msg-catcher' if catchlen == 1 else 'msg-catchers'
        catcherstr = '({} {} set.)'.format(catchlenstr, catchplural)
        print_status('No messages have been caught. {}'.format(catcherstr))
        return False


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
            print('\nCommand description for '
                  '{}:'.format(color_text('blue', cmdname)))
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
        # If it is an integer, special handling is needed.
        try:
            intval = int(boldtext)  # noqa
            boldfmt = color_text('red', '({})'.format(boldtext), bold=True)
        except ValueError:
            # normal handling.
            boldfmt = color_text('red', boldtext, bold=True)
        # Formatted normal message parts.
        msgfmt = [color_text('red', s) if s else '' for s in msgpart]
        # Final formatted message.
        msg = boldfmt.join(msgfmt)
    else:
        # Normal message.
        msg = '{}\n'.format(color_text('red', msg))

    # Append xtools so you know where this error is coming from.
    msg = '\n{}{}'.format(color_text('grey', 'xtools: '), msg)
    # Print formatted message.
    print(msg)

    # Print exception.
    if exc:
        print(color_text('red', '\n{}'.format(exc)))


def print_evalresult(cquery, coutput, **kwargs):
    """ Format eval code-output for chat before sending,
        or format for screen output.
    """
    chat = kwargs.get('chat', False)
    chatnick = kwargs.get('chatnick', None)
    resultonly = kwargs.get('resultonly', False)
    if chat:
        # Send to channel as user.
        queryfmt = cquery.replace('\n', '\\n')
        # Ensure ; is at the end of the query, to help separate lines like:
        # 5 == 5; == True, instead of 5 == 5 == True (which reads as False.)
        if not queryfmt.endswith(';'):
            queryfmt = '{};'.format(queryfmt)

        if resultonly:
            # don't include the query in the msg.
            chanmsg = coutput
        else:
            # include query; == result in the msg.
            chanmsg = '{} == {}'.format(queryfmt, coutput)
        # add directed message nick if given.
        if chatnick:
            chanmsg = '{}: {}'.format(chatnick, chanmsg)
        print_tochan(chanmsg)
    else:
        # Print to screen.
        print_status('Code Output:')
        print(coutput)


def print_evalerror(cquery, eoutput, **kwargs):
    """ Format eval error msg for chat before sending,
        or format for printing to screen.
    """
    chat = kwargs.get('chat', False)
    chatnick = kwargs.get('chatnick', None)
    resultonly = kwargs.get('resultonly', False)
    if chat:
        # Format chat msg, so its not too long.
        lastline = eoutput.split('\\n')[-1]
        # send to usual output printer/displayer.
        print_evalresult(cquery,
                         lastline,
                         chat=chat,
                         chatnick=chatnick,
                         resultonly=resultonly)
    else:
        # Not a chat send, no trimming is needed.
        errorsfmt = eoutput.replace('\\n', '\n')
        print_error('Code Error:\n{}'.format(errorsfmt))


def print_ignored_msgs():
    """ Prints all ignored messages for this session. """

    if not IGNORED_MSGS:
        print_status('No messages have been ignored.')
        return False

    # Print ignored messages.
    msglenstr = color_text('blue', str(len(IGNORED_MSGS)), bold=True)
    msgplural = 'message' if len(IGNORED_MSGS) == 1 else 'messages'
    print_status('You have {} ignored {}:\n'.format(msglenstr, msgplural))
    sortkey = lambda k: k['time']
    chanspace = longest([k['channel'] for k in IGNORED_MSGS])
    nickspace = longest([k['nick'] for k in IGNORED_MSGS])
    for msg in sorted(IGNORED_MSGS, key=sortkey):
        print_saved_msg(msg, chanspace=chanspace, nickspace=nickspace)
    return True


def print_ignored_nicks():
    """ Prints all ignored nicks. """

    if not IGNORED_NICKS:
        print_status('No nicks are being ignored.')
        return True

    ignorelenstr = str(len(IGNORED_NICKS))
    msglenstr = str(len(IGNORED_MSGS))
    statusmsg = ('Ignoring {} nicks ({} ignored msgs):'.format(
        color_text('blue', ignorelenstr),
        color_text('blue', msglenstr))
    )
    print_status(statusmsg)
    nicksortkey = lambda k: IGNORED_NICKS[k]['index']
    for nick in sorted(IGNORED_NICKS.keys(), key=nicksortkey):
        istr = str(IGNORED_NICKS[nick]['index'] + 1)
        line = '    {}: {}'.format(color_text('blue', istr, bold=True),
                                   color_text('blue', nick))
        print(line)
    return True


def print_tochan(msg, channel=None):
    """ Prints a message as the user to a channel. 
        If no channel is given, the current channel is used.
    """

    if not msg:
        print_error('No msg to send to channel.')
        return False

    if not channel:
        channel = xchat.get_context().get_info('channel')
    if not channel:
        print_error('No channel to send msg to.')
        return False

    xchat.command('MSG {} {}'.format(channel, msg))


def print_saved_msg(msg, chanspace=16, nickspace=16):
    """ Print a single saved msg from IGNORED_MSGS, or CAUGHT_MSGS.
        Must be the actual msg, not the msg id.
        from IGNORED_MSGS, or CAUGHT_MSGS[msgid].
    """

    msgtime = '({})'.format(color_text('grey', msg['time']))
    chan = '[{}]'.format(color_text('green', msg['channel'])).ljust(chanspace)
    # strip color from nick, and add our own.
    nick = remove_mirc_color(msg['nick'])
    if 'action' in msg['type']:
        nick = color_text('darkblue', nick.ljust(nickspace))
        # user action, add a big * on it.
        nick = '{}{}'.format(color_text('red', '*', bold=True), nick)
    else:
        # normal channel msg
        nick = color_text('darkblue', nick.ljust(nickspace + 1))

    if 'hilight' in msg['type']:
        # highlighted msg.
        msgtext = color_text('red', msg['msg'])
    else:
        # normal
        msgtext = msg['msg']
    print('{} {} {}: {}'.format(msgtime,
                                chan,
                                nick,
                                msgtext))


def print_status(msg):
    """ Print an xtools status message. """

    finalmsg = '\n{} {}'.format(color_text('grey', 'xtools:'), msg)
    print(finalmsg)


def print_version():
    """ Print xtools version. """

    print(color_text('blue', VERSIONSTR, bold=True))


def print_xtools(s):
    """ Print to the [xchat] tab/window """

    # Find existing xchat tab, or open a new one.
    context = get_xtools_window()
    if context is None:
        # Can't find xtools tab (timed out), print to the current tab.
        print(s)
    else:
        # print to xtools tab.
        context.prnt(s)


def remove_catcher(catcherstr):
    """ Removes a msg-catcher by string. """
    global MSG_CATCHERS

    def get_key(kstr):
        if kstr in MSG_CATCHERS.keys():
            return kstr
        else:
            # Try by index.
            try:
                intval = int(kstr)
            except:
                return None
            for msg in MSG_CATCHERS.keys():
                msgindex = MSG_CATCHERS[msg]['index']
                if msgindex == (intval - 1):
                    return msg

            return None

    removed_catchers = []
    for msg in catcherstr.split():
        msgkey = get_key(msg)
        if msgkey:
            # Good key, remove it.
            MSG_CATCHERS.pop(msgkey)
            removed_catchers.append(msgkey)
        else:
            print_error('Can\'t find that in the msg-catcher list: '
                        '{}'.format(msg),
                        boldtext=msg)
            continue

    # Fix indexes
    build_catcher_indexes()
    # Return status.
    if removed_catchers and save_catchers() and save_prefs():
        return removed_catchers
    else:
        return False


def remove_ignored_nick(nickstr):
    """ Removes an ignored nick by name. """
    global IGNORED_NICKS

    def get_key(kstr):
        if kstr in IGNORED_NICKS.keys():
            return kstr
        else:
            # Try by index.
            try:
                intval = int(kstr)
            except:
                return None
            for nick in IGNORED_NICKS.keys():
                nickindex = IGNORED_NICKS[nick]['index']
                if nickindex == (intval - 1):
                    return nick

            return None

    removed_nicks = []
    for nick in nickstr.split():
        nickkey = get_key(nick)
        if nickkey:
            # Good key, remove it.
            IGNORED_NICKS.pop(nickkey)
            removed_nicks.append(nickkey)
        else:
            print_error('Can\'t find that in the ignored list: '
                        '{}'.format(nick),
                        boldtext=nick)
            continue

    # Fix indexes
    build_ignored_indexes()
    # Return status.
    if removed_nicks and save_ignored_nicks() and save_prefs():
        return removed_nicks
    else:
        return False


def remove_mirc_color(text):
    """ Removes color code from text
    """
    # This function can be replaced with xchat.strip everywhere its called
    return xchat.strip(text)


def save_catchers():
    """ Save msg-catchers in preferences. """
    global SETTINGS

    if MSG_CATCHERS:
        catcher_str = '{|}'.join(list(MSG_CATCHERS.keys()))
        SETTINGS['msg_catchers'] = catcher_str
    else:
        # no msg catchers
        if 'msg_catchers' in SETTINGS.keys():
            SETTINGS.pop('msg_catchers')
    return True


def save_ignored_nicks():
    """ Save ignored nicks in preferences. """
    global SETTINGS

    if IGNORED_NICKS:
        ignored_str = ','.join(list(IGNORED_NICKS.keys()))
        SETTINGS['ignored_nicks'] = ignored_str
    else:
        # nick list is empty.
        if 'ignored_nicks' in SETTINGS.keys():
            SETTINGS.pop('ignored_nicks')

    return True


def save_prefs():
    """ Saves SETTINGS to preferences file. """
    try:
        with open(CONFIG_FILE, 'w') as fwrite:
            for opt, val in SETTINGS.items():
                if val:
                    fwrite.write('{} = {}\n'.format(opt, val))
            fwrite.flush()
        return True
    except (IOError, OSError) as exio:
        # Error writing/opening preferences.
        print_error('Can\'t save preferences to: {}'.format(CONFIG_FILE),
                    boldtext=CONFIG_FILE,
                    exc=exio)
        return False


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


# Commands -------------------------------------------------------------------

def cmd_catch(word, word_eol, userdata=None):
    """ Handles the /CATCH command to add/remove or list caught msgs. """

    word, argd = get_flag_args(word, [('-c', '--clear', False),
                                      ('-d', '--delete', False),
                                      ('-h', '--help', False),
                                      ('-l', '--list', False),
                                      ('-m', '--msgs', False),
                                      ('-r', '--remove', False),
                                      ])
    cmdname = word[0]
    cmdargs = get_cmd_rest(word)
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL
    elif argd['--clear']:
        if clear_catchers():
            print_status('Catch list cleared.')
    elif argd['--delete']:
        if clear_caught_msgs():
            print_status('Caught messages cleared.')
    elif argd['--list']:
        print_catchers()
    elif argd['--msgs']:
        print_caught_msgs()
    elif argd['--remove']:
        removed = remove_catcher(cmdargs)
        if removed:
            remstr = color_text('blue', ', '.join(removed), bold=True)
            print_status('Removed {} from the catch-msg list.'.format(remstr))
    elif cmdargs:
        added = add_catcher(cmdargs)
        if added:
            addedstr = color_text('blue', ', '.join(added), bold=True)
            print_status('Added {} to the catch-msg list.'.format(addedstr))
    else:
        # default
        print_caught_msgs()

    return xchat.EAT_ALL


def cmd_catchers(word, word_eol, userdata=None):
    """ Shortcut command for /catch --list """
    if word[1:]:
        # If the command has args its just an alias for /CATCH
        return cmd_catch(word, word_eol, userdata=userdata)
    else:
        # No args, default action is to list catchers instead of caught msgs.
        print_catchers()
        return xchat.EAT_ALL


def cmd_eval(word, word_eol, userdata=None):
    """ Evaluates your own python code, prints query and result
        to the screen or sends the code and output directly to the channel
        as a msg from you.
        Example:
            cmd_eval(['/eval', '-c', 'print("myoutput")'])
            # does:
            # /msg <currentchannel> myoutput
            cmd_eval(['/eval', 'print("private output")'])
            # prints "private output" to your chat window only.
    """

    # Get args from command.
    word, argd = get_flag_args(word, (('-c', '--chat'),
                                      ('-h', '--help'),
                                      ('-r', '--result'),
                                      ('-e', '--errors')))
    cmdname = word[0]
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL

    # Remove command from word.
    word = word[1:]
    if not word:
        print_error('No code to evaluate.')
        return xchat.EAT_ALL

    # Grab directed nick msg from word if available.
    msgnick = None
    if argd['--chat']:
        firstword = word[0]
        chanusers = xchat.get_context().get_list('users')
        if firstword.lower() in [n.nick.lower() for n in chanusers]:
            # first word is a nick, save it and remove it from the query.
            msgnick = firstword
            word = word[1:]

    # Grab code query, if -c and name were only provided its an error.
    query = ' '.join(word) if word else None
    if not query:
        print_error('No code to evaluate.')
        return xchat.EAT_ALL

    # Fix newlines
    # allow users to type \\n to escape real newlines,
    # but use \n as an actual newline (as if ENTER had been pressed)
    query = query.replace('\\\\n', '${nl}')
    query = query.replace('\\n', '\n')
    query = query.replace('${nl}', '\\n')
    # Choose exec mode.
    if '\n' in query:
        mode = 'exec'
        if not query.endswith('\n'):
            query = '{}\n'.format(query)
    else:
        mode = 'single'

    # Make an interpreter to run the code.
    compiler = InteractiveInterpreter()
    
    # stdout/stderr will be captured, for optional chat output.
    with StdErrCatcher() as errors:
        with StdOutCatcher() as captured:
            # execute/evaluate the code.
            incomplete = compiler.runsource(query, symbol=mode)

    # Incomplete source code.
    if incomplete:
        # Code will not compile.
        warnmsg = 'Incomplete source.'
        print_error(warnmsg, boldtext=warnmsg)
    # Print any errors.
    elif errors.output:
        # Send error output. Only send to chat if the -c flag is given AND
        # the --errors flag is given. Otherwise print to screen.
        print_evalerror(query, errors.output,
                        chat=(argd['--chat'] and argd['--errors']),
                        chatnick=msgnick,
                        resultonly=argd['--result'])
    # Code had output.
    elif captured.output:
        # Send good output to screen or chat (with or without nick or query)
        print_evalresult(query, captured.output,
                         chat=argd['--chat'],
                         chatnick=msgnick,
                         resultonly=argd['--result'])
    else:
        # No command output, user didn't print() or something.
        print_error('No Output.')
    return xchat.EAT_ALL


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
                                      ('-h', '--help'),
                                      ('-n', '--nick')])

    cmdname = word[0]
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL

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
            nickraw = xchat.strip(nick)
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
    word, argd = get_flag_args(word, [('-a', '--all'),
                                      ('-h', '--help'),
                                      ('-c', '--count')])
    cmdname = word[0]
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL

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

    # Format results.
    color_result = lambda u: '{} - ({})'.format(color_text('blue', u.nick),
                                                color_text('purple', u.host))
    userfmt = [color_result(u) for u in userlist]
    print('    {}'.format('\n    '.join(userfmt)))
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
    word, argd = get_flag_args(word,
                               [('-H', '--host'),
                                ('-h', '--help'),
                                ('-o', '--onlyhost'),
                                ('-a', '--all')])
    cmdname = word[0]
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL

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
    if not query:
        print_error('No query, use /listusers instead.')
        return xchat.EAT_ALL
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
            if argd['--all'] and userchannels:
                newresults = []
                for userinf in [n for n in results]:
                    if userinf.nick in userchannels.keys():

                        newresults.append((userinf.nick,
                                           userinf.host,
                                           ', '.join(sorted_chans(userinf))))
                    else:
                        newresults.append((userinf.nick, userinf.host, ''))
                # Helper function for formatting.
                formatter = lambda t: '{} - ({})\n{}{}'.format(colornick(t[0]),
                                                               colorhost(t[1]),
                                                               (' ' * 8),
                                                               colorchan(t[2]))
                # Format the new results.
                resultsfmt = [formatter(i) for i in newresults]
            else:
                # Current channel only, no host.
                formatter = lambda u: '{} - ({})'.format(colornick(u.nick),
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
        # TODO: open a new window with QUERY, print long results there.
        print('Found {} {}{}: {}\n'.format(resultstr,
                                           pluralnicks,
                                           channellenstr,
                                           formattednicks))
    else:
        print(color_text(color='red', bold=True, text='No nicks found.\n'))

    return xchat.EAT_ALL


def cmd_whitewash(word, word_eol, userdata=None):
    """ Prints a lot of whitespace to 'clear' the chat window. """

    word, argd = get_flag_args(word, ('-h', '--help'))
    cmdname = word[0]
    cmdargs = get_cmd_rest(word)
    if argd['--help']:
        print_cmdhelp(cmdname)
        return xchat.EAT_ALL
    elif cmdargs:
        try:
            linecnt = int(cmdargs)
        except ValueError:
            print_error('Invalid number given!')
            return xchat.EAT_ALL
    else:
        # Default amount.
        linecnt = 50
    # Minimum amount.
    if linecnt < 1:
        linecnt = 1
    elif linecnt > 250:
        print_error('Maximum amount exceeded, defaulting to 250.')
        linecnt = 250

    # Print a bunch of blank lines.
    print_status('Washing the window with {} lines.'.format(str(linecnt)))
    print('\n' * linecnt)
    return xchat.EAT_ALL


def cmd_xignore(word, word_eol, userdata=None):
    """ Handles the /XIGNORE command to add/remove or list ignored nicks. """
    global IGNORED_MSGS

    word, argd = get_flag_args(word, [('-c', '--clear', False),
                                      ('-d', '--delete', False),
                                      ('-h', '--help', False),
                                      ('-l', '--list', False),
                                      ('-m', '--msgs', False),
                                      ('-r', '--remove', False),
                                      ])
    cmdargs = get_cmd_rest(word)

    if argd['--clear']:
        if clear_ignored_nicks():
            print_status('Ignore list cleared.')
    elif argd['--delete']:
        IGNORED_MSGS = deque(maxlen=MAX_IGNORED_MSGS)
        print_status('Deleted all ignored messages.')
    elif argd['--help']:
        print_cmdhelp('xignore')
    elif argd['--list']:
        print_ignored_nicks()
    elif argd['--msgs']:
        print_ignored_msgs()
    elif argd['--remove']:
        removed = remove_ignored_nick(cmdargs)
        if removed:
            remstr = color_text('blue', ', '.join(removed), bold=True)
            print_status('Removed {} from the ignored list.'.format(remstr))
    elif cmdargs:
        added = add_ignored_nick(cmdargs)
        if added:
            addedstr = color_text('blue', ', '.join(added), bold=True)
            print_status('Added {} to the ignored list.'.format(addedstr))
    else:
        # default
        print_ignored_nicks()

    return xchat.EAT_ALL


def cmd_xtools(word, word_eol, userdata=None):
    """ Shows info about xtools. """

    word, argd = get_flag_args(word, [('-v', '--version'),
                                      ('-d', '--desc'),
                                      ('-h', '--help'),
                                      ('-cd', '--colordemo'),
                                      ])
    cmdargs = get_cmd_rest(word)

    # Version only
    if argd['--version']:
        print_version()
        return xchat.EAT_ALL

    # Command description or descriptions.
    elif argd['--desc']:
        print_cmddesc(cmdargs)
        return xchat.EAT_ALL

    # Command help.
    elif argd['--help']:
        print_cmdhelp(cmdargs)
        return xchat.EAT_ALL

    # Undocumented test for color_code.
    elif argd['--colordemo']:
        print_colordemo()
        return xchat.EAT_ALL

    # No args, default behavior
    print_cmddesc(cmdargs)
    return xchat.EAT_ALL


def filter_chanmsg(word, word_eol, userdata=None):
    """ Filter Channel Messages. """
    global IGNORED_MSGS

    # Ignoring messages is easy, just save it and return EAT_ALL.
    msgnick = word[0]
    for nickkey in IGNORED_NICKS.keys():
        nickpat = IGNORED_NICKS[nickkey]['pattern']
        if nickpat.search(msgnick):
            # Ignore this message.
            add_message(IGNORED_MSGS.append,
                        msgnick, word_eol[1], msgtype=userdata)
            return xchat.EAT_ALL

    # Caught msgs, needs add_caught_msg because of other scripts emitting
    # duplicate msgs. The add_caught_msg function handles this.
    for catchmsg in MSG_CATCHERS.keys():
        msgpat = MSG_CATCHERS[catchmsg]['pattern']
        if msgpat.search(word_eol[1]):
            add_message(add_caught_msg,
                        msgnick, word_eol[1], msgtype=userdata)
            return xchat.EAT_NONE
    # Nothing will be done to this message.
    return xchat.EAT_NONE


def filter_message(word, word_eol, userdata=None):
    """ Filters all channel messages. """

    filter_funcs = {'Channel Message': filter_chanmsg,
                    'Channel Msg Hilight': filter_chanmsg,
                    'Channel Action': filter_chanmsg,
                    'Channel Action Hilight': filter_chanmsg,
                    }

    if userdata in filter_funcs.keys():
        # This event has a function.
        return filter_funcs[userdata](word, word_eol, userdata=userdata)

    return xchat.EAT_NONE

# START OF SCRIPT ------------------------------------------------------------

# List of command names/functions
# (all keys should also be in cmd_help, and vice versa)
commands = {
    'catch': {'desc': 'Catch messages based on content.',
                      'func': cmd_catch,
                      'enabled': True},
    'catchers': {'desc': 'Shortcut for /CATCH --list, lists all msg-catchers',
                 'func': cmd_catchers,
                 'enabled': True},
    'eval': {'desc': 'Evaluate python code. Can send output to chat.',
                     'func': cmd_eval,
                     'enabled': True},
    'finduser': {'desc': '',
                         'func': cmd_searchuser,
                         'enabled': True},
    'findtext': {'desc': 'Search chat text to see who said what.',
                         'func': cmd_findtext,
                         'enabled': True},
    'listusers': {'desc': 'List users in all rooms or current room.',
                          'func': cmd_listusers,
                          'enabled': True},
    'searchuser': {'desc': 'Find users by name or part of a name.',
                           'func': cmd_searchuser,
                           'enabled': True},
    'wash': {'desc': 'alias',
                     'func': cmd_whitewash,
                     'enabled': True},
    'whitewash': {'desc': ('Prints a lot of whitespace to clear the '
                           'chat window.'),
                  'func': cmd_whitewash,
                  'enabled': True},
    'whosaid': {'desc': '',
                        'func': cmd_findtext,
                        'enabled': True},
    'xignore': {'desc': 'Add/Remove or list ignored nicks.',
                        'func': cmd_xignore,
                        'enabled': True},
    'xtools': {'desc': 'Show command info or xtools version.',
                       'func': cmd_xtools,
                       'enabled': True},
}

# Help for commands
cmd_help = {'catch':
            ('Usage: /CATCH <pattern>\n'
             '       /CATCH -r <pattern>\n'
             '       /CATCH [-c | -d | -l | -m]\n'
             'Options:\n'
             '    <pattern>    : A word or regex pattern, if found in\n'
             '                   a message it causes the msg to be\n'
             '                   saved. You can retrieve the msgs with\n'
             '                   the -m flag.\n'
             '    -c,--clear   : Clear the msg-catcher list.\n'
             '    -d,--delete  : Delete all caught messages.\n'
             '    -l,--list    : List all msg-catcher patterns.\n'
             '    -m,--msgs    : Print all caught messages.\n'
             '    -r,--remove  : Remove msg-catcher by number or text.\n'
             '\n    * With no arguments passed, all caught msgs are listed.'
             '\n    * You can pass several space-separated catchers.'),
            'catchers':
            ('Usage: /CATCHERS [/catch args]\n'
             '    ...shortcut for /CATCH --list, lists all msg-catchers.\n'
             '    * any arguments given to this command are sent to the\n'
             '      /CATCH command.'),
            'eval':
            ('Usage: /EVAL [-c [nick] [-e] [-r]] <code>\n'
             'Options:\n'
             '    -c [n],--chat [n] : Send as msg to current channel.\n'
             '                        Newlines are replaced with \\\\n,\n'
             '                        and long output is truncated.\n'
             '                        If a nick (n) is given, mention the\n'
             '                        nick in the message.\n\n'
             '                        * Nick must come before eval code,\n'
             '                          and nick must be present in the\n'
             '                          current channel.\n'
             '    -e,--errors       : Force send any errors to chat.\n'
             '                        This overrides default behavior of\n'
             '                        cancelling chat-sends when exceptions\n'
             '                        are raised.\n'
             '                        Sends the last line of the error msg\n'
             '                        to chat, usually the Exception string.\n'
             '    -r,--result       : When chat-sending, send result only.\n'
             '                        The original query is not sent.\n\n'
             '    ** Warning: This is an unprotected eval, it will eval\n'
             '                whatever code you give it. It only accepts\n'
             '                input from you, so you only have yourself to\n'
             '                blame when something goes wrong.\n'
             '                It is smarter than the plain eval() function,\n'
             '                which makes it more dangerous too.\n\n'
             '    ** DO NOT import os;os.system(\'rm -rf /\')\n'
             '    ** DO NOT print(open(\'mypassword.txt\').read())\n'
             '    ** DO NOT do anything you wouldn\'t do in a python \n'
             '       interpreter.'
             ),
            'findtext':
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
             '    -H,--host      : Search host also.\n' +
             '    -o,--onlyhost  : Only search hosts, not nicks.\n'),
            'whitewash':
            ('Usage: /WHITEWASH [number_of_lines]\n'
             'Options:\n'
             '    number_of_lines  : Print the specified amount of lines.\n'
             '                       Default: 50'),
            'xignore':
            ('Usage: /XIGNORE <nick>\n'
             '       /XIGNORE -r <nick>\n'
             '       /XIGNORE [-c | -d | -l | -m]\n'
             'Options:\n'
             '    <nick>       : Regex or text for nick to ignore.\n'
             '    -c,--clear   : Clear the ignored list.\n'
             '    -d,--delete  : Delete all ignored messages.\n'
             '    -l,--list    : List all ignored nicks.\n'
             '    -m,--msgs    : Print all ignored messages.\n'
             '    -r,--remove  : Remove nick by number or name.\n'
             '\n    * With no arguments passed, all ignored nicks are listed.'
             '\n    * You can pass several space-separated nicks.'
             ),
            'xtools':
            ('Usage: /XTOOLS [-v] | [[-d | -h] <cmdname>]\n'
             'Options:\n'
             '    <cmdname>               : Show help for a command.\n'
             '                              (same as /help cmdname)\n'
             '    -d [cmd],--desc [cmd]   : Show description for a command,\n'
             '                              or all commands.\n'
             '    -h [cmd],--help [cmd]   : Show help for a command,\n'
             '                              or all commands.\n'
             '    -v,--version            : Show version.\n'
             '\n    * If no options are given, -d is assumed.'),
            }
# Command aliases
# {'aliasname': {'originalcmd': {'helpfix': ('REPLACE', 'REPLACEWITH')}}}
cmd_aliases = {'finduser': {'searchuser': {'helpfix': ('SEARCH', 'FIND')},
                            },
               'whosaid': {'findtext': {'helpfix': ('FINDTEXT', 'WHOSAID')},
                           },
               'wash': {'whitewash': {'helpfix': ('WHITEWASH', 'WASH')}
                        },
               }

# Load Colors
COLORS = build_color_table()

# Load Preferences
load_prefs()
load_ignored_nicks()
load_catchers()

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

# Hook into channel msgs
for eventname in ('Channel Message', 'Channel Msg Hilight',
                  'Channel Action', 'Channel Action Hilight', 'Your Message'):
    xchat.hook_print(eventname, filter_message, userdata=eventname)

# Load Status Message
print(color_text(color='blue',
                 text='{} loaded.'.format(VERSIONSTR)))
