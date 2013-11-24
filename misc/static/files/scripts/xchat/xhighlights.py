#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""xhighlights.py

    Highlights URLS in XChat...

    -Christopher Welborn
"""

__module_name__ = 'xhighlights'
__module_version__ = '0.3.7'
__module_description__ = 'Highlights URLs and Nicks in the chat window.'
VERSIONSTR = '{} v. {}'.format(__module_name__, __module_version__)

import os
import re
import xchat

# Regex for matching a link..
link_re = re.compile('^http\:|^https\:|^ftp|^www\.|\.com$|\.org$|[\w\d]\.net$')


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


def cmd_xhighlights(word, word_eol, userdata):
    """ Handles /XHIGHLIGHTS command.
        Allows you to set default colors/styles.
    """

    # Clean word and get flags for command.
    word, argd = get_flag_args(word, [('-c', '--colors', False),
                                      ('-l', '--link', False),
                                      ('-n', '--nick', False),
                                      ])
    cmdargs = get_cmd_rest(word).lower().strip()

    # Just print styles..
    if argd['--colors']:
        print_styles()
        return xchat.EAT_ALL

    # Check ambiguous args.
    if argd['--link'] and argd['--nick']:
        print_error('Cannot use --link and --nick at the same time.')
        return xchat.EAT_ALL

    # If no style was passed, just print the current style.
    if not cmdargs:
        if not (argd['--link'] or argd['--nick']):
            # No args at all. Print all styles.
            print_currentstyles()
        else:
            # Print single style, for whatever arg was passed.
            print_currentstyles(link=argd['--link'], nick=argd['--nick'])
        return xchat.EAT_ALL

    # Set nick code.
    if argd['--nick']:
        set_style(cmdargs, 'nick')
    # Set link style.
    elif argd['--link']:
        set_style(cmdargs, 'link')

    return xchat.EAT_ALL


def color_code(color, suppresswarning=False):
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
        if suppresswarning:
            return None
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


def highlight_word(s, style='link', ownmsg=False):
    """ Highlight a single word (string) in the prefferred style
        s     :  The word (string) to highlight.
        style : Type of word, either 'nick' or 'link'
    """
    if not style:
        style = 'link'
    # Own messages are grey on my system.
    # so grey is normal if its my own message.
    # Otherwise, black is normal (actually 'normal' is normal)
    colornormal = Codes.ownmsg if ownmsg else Codes.normal
    resetcode = Codes.normal + colornormal if ownmsg else colornormal

    if style == 'link':
        # LINK Highlighting
        stylecode = Codes.link
    elif style == 'nick':
        # NICK Highlighting
        stylecode = Codes.nick
    else:
        # Not implemented
        stylecode = Codes.normal
    formatted = '{style}{word}{reset}'.format(style=stylecode,
                                              word=s,
                                              reset=resetcode)
    return formatted


def load_user_color(stylename):
    """ Loads colors from preferences, or uses defaults on error. """
    stylename = stylename.lower().strip()
    user_pref = pref_get('xhighlights_{}'.format(stylename))
    if user_pref:
        if set_style(user_pref, stylename):
            print_status('Loaded {} from preferences: {}'.format(stylename,
                                                                 user_pref))
        else:
            # Failure
            print_status('Default {} style will be used.'.format(stylename))
            try:
                defaultcode = getattr(Codes, 'default{}'.format(stylename))
                setattr(Codes, stylename, defaultcode)
            except Exception as ex:
                print_error('Unable to set default style: '
                            '{}'.format(stylename),
                            exc=ex)
            return False
    return True


def message_filter(word, word_eol, userdata):
    """ Filter all messages coming into the chat window.
        Arguments:
            word    : List of data [nick, message]
            word_eol: Same as word except [nick message, message]
            userdata: The event this message came from (used to emit_print())
    """

    # Get list of nicks.
    userslist = [u.nick for u in xchat.get_list('users')]

    # Get nick for message, and current users nick
    msgnick = word[0]

    # The actual message.
    msg = word[1]
    # Words in the actual message.
    msgwords = msg.split(' ')
    # Flag for when messsages are modified
    # (otherwise we don't emit or EAT anything.)
    highlighted = False

    normalmsg = (userdata != 'Channel Msg Hilight')
    usernick = (xchat.get_context()).get_info('nick')
    msgnick = remove_mirc_color(word[0])
    # Determine if this is the users own message
    # (changes highlight_word() settings)
    userownmsg = (usernick == msgnick)

    for i in range(len(msgwords)):
        # Current word being looked at.
        eachword = msgwords[i]
        # Word is users own nick name?
        ownnick = (eachword == usernick) or (eachword[:-1] == usernick)
        # Word is any user name?
        nickword = (eachword in userslist) or (eachword[:-1] in userslist)

        # Link highlighting
        linkmatch = link_re.search(eachword)
        if linkmatch:
            # Highlight it
            msgwords[i] = highlight_word(eachword, 'link', ownmsg=userownmsg)
            highlighted = True

        # Nick highlighting
        # (Don't highlight your own nick, thats for Channel Msg Hilight)
        elif (normalmsg and (not ownnick)) and nickword:
            msgwords[i] = highlight_word(eachword, 'nick', ownmsg=userownmsg)
            highlighted = True

    # Replace old message.
    word[1] = ' '.join(msgwords)

    # Print to the chat window.
    if highlighted:
        # Build args for emit_print
        # (userdata=Event Name, word = Modifed Message)
        emitargs = [userdata] + word
        # Emit modified message (with highlighting)
        (xchat.get_context()).emit_print(*emitargs)
        # Block normal handling of this message.
        return xchat.EAT_ALL
    else:
        # Nothing was done to this message
        return xchat.EAT_NONE


def pref_get(opt):
    """ Retrieves an XChat preference. """

    # Xchat has to be reloaded after prefs are set,
    # The regular xchat.get_prefs() will not see anything written to the
    # file since loading xchat. Also, the '/set' command doesn't work on
    # any preference xchat 'can't see' (has been written after xchat load.)
    # So we need to manually retrieve this preference.
    # This way reloading xhighlights will get latest pref changes
    # whether xchat has been reloaded or not.

    # Get xchat prefs file.
    prefsfile = os.path.expanduser('~/.xchat2/xchat.conf')
    if not os.path.isfile(prefsfile):
        print_error('Can\'t find xchat.conf: {}'.format(prefsfile),
                    boldtext=prefsfile)
        return False

    # Load prefs data.
    try:
        with open(prefsfile, 'r') as fread:
            allprefs = fread.readlines()
    except (IOError, OSError) as ex:
        print_error('Unable to open xchat.conf: {}'.format(prefsfile),
                    exc=ex,
                    boldtext=prefsfile)
        return False

    existingopt = None
    for line in allprefs:
        if line.startswith(opt):
            # Found the line, retrieve its whole content.
            existingopt = line
            break

    # No option found.
    if not existingopt:
        return None

    # Parse option.
    if '=' in existingopt:
        val = existingopt.strip('\n').split('=')[1].strip()
        return val
    else:
        # Bad config
        return None


def pref_set(opt, val):
    """ Sets an XChat preference. """

    # The '/set' command will not work here unless this setting
    # has been written to xchat.conf BEFORE startup. There is also no way
    # to detect the response from 'xchat.command('set')'. This means
    # we have to manually write this setting to file, and make sure
    # pref_get() reads the actual file, not just xchat.get_prefs().

    # Get xchat prefs file.
    prefsfile = os.path.expanduser('~/.xchat2/xchat.conf')
    if not os.path.isfile(prefsfile):
        print_error('Can\'t find xchat.conf: {}'.format(prefsfile),
                    boldtext=prefsfile)
        return False

    # Load prefs data.
    try:
        with open(prefsfile, 'r') as fread:
            allprefs = fread.readlines()
    except (IOError, OSError) as ex:
        print_error('Unable to open xchat.conf: {}'.format(prefsfile),
                    exc=ex,
                    boldtext=prefsfile)
        return False

    # new options line for xchat.conf.
    optline = '{} = {}'.format(opt, str(val))

    # Search preferences for this option.
    existingopt = None
    for line in allprefs:
        if line.startswith(opt):
            # Found the line, retrieve its whole content.
            existingopt = line
            break

    # Existing pref.
    if existingopt:
        if existingopt == optline:
            # Pref already set.
            return True

        allprefs[allprefs.index(existingopt)] = optline
    # New pref.
    else:
        allprefs.append(optline)

    # Remove blank lines..
    while '' in allprefs:
        allprefs.remove('')
    while '\n' in allprefs:
        allprefs.remove('\n')

    # Write preferences.
    try:
        with open(prefsfile, 'w') as fwrite:
            fwrite.writelines(allprefs)
            fwrite.write('\n')
            return True
    except (IOError, OSError) as ex:
        print_error('Unable to write to xchat.conf: {}'.format(prefsfile),
                    exc=ex,
                    boldtext=prefsfile)
        return False


def print_styles():
    """ Print all available styles. """

    print('Available styles:')
    for cname in sorted(COLORS.keys(), key=lambda x: COLORS[x]['index']):
        cindex = str(COLORS[cname]['index'])
        if len(cindex) == 1:
            cindex = '0{}'.format(cindex)
        print('    {} : {}'.format(cindex, color_text(cname, cname)))
    print('')


def print_currentstyles(link=True, nick=True):
    """ Print the current settings. """

    if not (link or nick):
        return False

    if link and nick:
        header = 'Current styles are:'
    else:
        header = 'Current link style:' if link else 'Current nick style:'
    print('\n{}'.format(header))
    if link:
        print('    {}Link'.format(Codes.link))
    if nick:
        print('    {}Nick'.format(Codes.nick))


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


def print_status(s):
    """ Prints a formatted status message. """

    print('\n{}\n'.format(color_text('green', s)))

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


def set_style(userstyle, stylename=None, silent=False):
    """ Sets the current style for 'link' or 'nick' """

    userstyle = userstyle.lower().strip()
    stylename = stylename.lower().strip() if stylename else 'link'

    def parse_styles(txt):
        """ Parses comma-separated styles. """
        if ',' in txt:
            return [s.strip() for s in txt.split(',')]
        else:
            # single item
            return [txt.strip()]

    def try_stylecodes(styles):
        """ Trys to retrieve multiple style codes, and returns a string
            containing them.
        """

        final = ''
        for style in styles:
            stylecode = color_code(style, suppresswarning=True)
            if not stylecode:
                return None
            final = final + stylecode
        return final

    stylenames = parse_styles(userstyle)
    stylecodes = try_stylecodes(stylenames)
    if not stylecodes:
        print_error('Invalid style code: {}'.format(userstyle),
                    boldtext=userstyle)
        return False

    if stylename == 'link':
        Codes.link = stylecodes
    elif stylename == 'nick':
        Codes.nick = stylecodes
    else:
        print_error('Invalid style name: {}'.format(stylename),
                    boldtext=stylename)
        return False

    # Save preference.
    if not pref_set('xhighlights_{}'.format(stylename), userstyle):
        print_error('Unable to save preference for {}.'.format(stylename))
        return False

    if not silent:
        print_status('Set style for {}: {}{}'.format(stylename,
                                                     stylecodes,
                                                     userstyle))
    return True

# START OF SCRIPT
# Load colors (must be loaded before class Codes()).
COLORS = build_color_table()


class Codes:

    """ Holds current highlight styles. """
    defaultlink = color_code('u') + color_code('blue')
    defaultnick = color_code('green')
    link = defaultlink
    nick = defaultnick
    ownmsg = color_code('darkgrey')
    normal = color_code('reset')

# Load user preferences.
for stylename in ('link', 'nick'):
    load_user_color(stylename)


# Commands and command help strings.
cmd_help = {'xhighlights':
            ('Usage: /XHIGHLIGHTS [-n [style] | -l [style]]\n'
             'Options:\n'
             '    -c,--colors            : Show available styles.'
             '    -l style,--link style  : Set link style by name/number.\n'
             '    -n style,--nick style  : Set nick style by name/number.\n'
             '\n    * style can be comma separated style names/numbers.\n'
             '    * if no style is given, the current style will be shown.\n'),
            }

commands = {'xhighlights': {'desc': 'Gets and sets options for xhighlights.',
                            'func': cmd_xhighlights,
                            'enabled': True,
                            },
            'highlights': {'desc': 'alias',
                           'func': cmd_xhighlights,
                           'enabled': True,
                           },
            }

# command aliases.
cmd_aliases = {'highlights': {'xhighlights': {'helpfix': ('XHIGH', 'HIGH')},
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

# Hook into channel msgs
for eventname in ('Channel Message', 'Channel Msg Hilight', 'Your Message'):
    xchat.hook_print(eventname, message_filter, userdata=eventname)


# Print status
print('{} loaded.'.format(color_text('blue', VERSIONSTR)))
