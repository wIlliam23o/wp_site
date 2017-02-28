#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
    Welborn Productions - Switches
    Turns features/settings on or off by replacing code or variable values.
    Meant to be single file executable, hopefully it doesn't get too messy.

    -Christopher Welborn <cj@welbornprod.com> 5-2-13
'''

# copies Switch() class, saves previous version while editing/building
# switches.
import copy
import sys
import os.path
import re  # for regex 'finders'

NAME = 'WpSwitch'
VERSION = '1.0.2-1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)

CHECK_DIRS = [os.path.abspath(sys.path[0])]
# Fix path.
try:
    import django_init
    if not django_init.init_django():
        print('\nUnable to initialize django environment!')
        sys.exit(1)
except ImportError:
    # Try django-style import.
    try:
        from scripts import django_init
    except ImportError as eximp:
        print('\nUnable to import django_init!\n{}'.format(eximp))
        sys.exit(1)

PROJECT_DIRS = [django_init.project_dir,
                django_init.scripts_dir,
                django_init.settings_dir,
                ]
CHECK_DIRS.extend(PROJECT_DIRS)

usage_str = """{version}

    usage: wpswitch <command> | <switch_name on|off|-|?|!|@> [options]

    commands:
              help : show the long help message
         -h,--help : show the usage help message
             names : list all switch names
            groups : list all groups and members
            status : list all switch names and state
            values : list all switch names and actual values
              full : list all switch names and actual lines
             files : list file names for targets and switches using them.

    switch operations:
                on : turn this switch on
               off : turn this switch off
                 - : toggle it's current state
                 + : increment version switch
                 ? : show it's current state (on|off)
                 ! : show it's actual code value
                 @ : show switches full text and value

    options:
      -d, --dryrun : dry run, don't modify any files (will print to console)
        -r, --real : show the real value when setting switches.

""".format(version=VERSIONSTR)

help_str = """
    wpswitch help:

    what is this?:
        wpswitch can modify/switch between two values for a single variable
        from the command line. you need to tell it what to look for, where to
        find it, and what the two possible values are. once the switches are
        configured, changing between debug and live mode in django is as easy
        as typing:
        wpswitch debug on
        or, toggling it's current state with:
        wpswitch debug -

    how it works:
        what's going on is wpswitch is looking in your switches for one named
        'debug', reading the file that you've assigned this switch to, and
        grabbing it's value. once the current value is known its just a simple
        text replace. when you run 'wpswitch debug on', it looks for what 'on'
        means for a switch called 'debug'. in this case 'on' means 'True'. the
        'debug' switch's 'finder' would be set to 'DEBUG =' or 'TEMPLATE_DEBUG
        = DEBUG =', this tells wpswitch what this switch is, so it can find it
        and switch between it's configured 'on' and 'off' values.
    """


class Switch(object):

    """ Holds info about a single switch,
        such as Name, Possible Values for On/Off,
        and the RegEx/Text needed to find the switch. """

    def __init__(
            self, filename=None, name=None, default_values=None,
            finder=None, description=None, group=None):
        """       Filename: File where we can find the switch
                            (with the finder text).
                            Must be in same directory, or relative path of
                            same directory.
                            ex: settings_local.py -or- /main/settings.py
                      Name: Name of switch
                            ex: "debug"
            Default Values: List/Tuple of values for On and Off.
                            (OnValue, OffValue)
                            ex: (True, False)
                    Finder: Text to find this switch, if it starts with and
                            ends with /, it's regex.
                            ex: "DEBUG = "
                                (works better on single line, otherwise
                                may break.)
                            ** Regex should only match a single switch!
                               multiple matching switches won't work!
               Description: A comment, or description about this switch.
                     Group: Name of the group this switch belongs to, or
                            None if not grouped.
        """

        if filename is None:
            self.filename = None
        else:
            self.filename = os.path.abspath(os.path.expanduser(filename))

        # allows setting multiple names for a switch ['database', 'db']
        if isinstance(name, (list, tuple)):
            self.aliases = name
            if len(name) > 0:
                # Use first name in the list
                self.name = name[0]
            else:
                self.name = None
        else:
            # Single name, or None.
            self.name = name
            self.aliases = None
        self.values = default_values
        self.finder = finder
        self.description = description
        self.group = group

    def __str__(self):
        """ string representation of switch """
        return str(self.name)

    def __repr__(self):
        """ representation of switch """
        return self.get_switch_str()

    def __eq__(self, other):
        if isinstance(other, Switch):
            return ((self.get_switch_str() == other.get_switch_str()) and
                    (self.group == other.group))
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    def get_switch_str(self):
        """ Returns the switch string,
            or what the switch should look like in the switches file.
        """

        if self.aliases is None:
            names = str(self.name)
        else:
            names = str(','.join(self.aliases))

        if self.values is None:
            values = str(self.values)
        else:
            values = str(','.join(self.values))

        return str(SWITCH_SEPARATOR.join((str(self.filename),
                                          names,
                                          values,
                                          str(self.finder),
                                          str(self.description))))

    def get_switch_id(self):
        """ Trying to find a unique identifier for switches. """

        if self.aliases is None:
            names = str(self.name)
        else:
            names = str(','.join(self.aliases))

        return str(SWITCH_SEPARATOR.join((str(self.filename), names)))

    def get_name(self):
        """ safely etrieves default name for this switch if aliases are given.
            Otherwise returns self.name
        """

        if self.aliases is None:
            if self.name:
                return self.name
            else:
                print_fail('This switch is not properly configured!\n'
                           '{}'.format(repr(self)))
        else:
            return self.aliases[0]

    def get_description(self):
        """ safely retrieves a description (returns 'None' string on failure)
        """
        return str(self.description)

    def on_value(self):
        """ Retrieves the expected value for "on" """

        return self.values[0]

    def off_value(self):
        """ Retrieves the expected value for "off" """

        return self.values[1]

    def convert_value(self, value):
        """ Just converts the verbose values to actual expected values,
            and vice-versa.
            example where sw = Switch():
                actual = self.convert_value(sw.get_state())
            ...if you wanted the actual value, not the converted actual value,
               you could just do this:
                actual_really = sw.get_state(actual_value=True)
            possible_values may not be a string.
        """

        possible_values = {'on': self.on_value(),
                           'off': self.off_value()}
        for skey in possible_values.keys():
            if str(value).lower() == str(skey).lower():
                return possible_values[skey]
            elif str(possible_values[skey]) == str(value):
                return skey
        return None

    def is_regex(self):
        """ Returns true if the finder text is a regex expression """

        if self.finder is not None:
            return (self.finder.startswith('/') and
                    self.finder.endswith('/') and
                    len(self.finder) > 2)

        return False

    def is_version(self):
        """ Returns true if this is a version switch (version incrementer) """

        return (self.values[0] == 'v-' and self.values[1] == 'v+')

    def finder_text(self):
        """ Just automatically removes the /'s if the finder is a regex,
            otherwise returns the finder.
        """

        if (self.is_regex()) and (self.finder is not None):
            return self.finder[1:-1]
        return self.finder

    def get_file_contents(self):
        """ Retrieves contents of switches file, using file.read() """

        filename = self.relative_filename()
        if filename is None:
            print_fail('Cannot find file for {}: {}'.format(
                self.get_name(),
                self.filename))

        try:
            with open(filename) as fread:
                contents = fread.read()
        except Exception as ex:
            print_fail('Cannot retrieve contents for {}: {}\nError: {}'.format(
                self.get_name(),
                self.filename,
                ex))
        # everything passed, return contents.
        return contents

    def get_switch_text(self, contents=None):
        """ retrieves actual code text for this switch.
            (for when regex is used, but also works for regular text.)
            contents is the switches file contents, if none is passed
            then file contents are retrieved. this is so functions can
            work on the same contents without reading/checking the file twice.
        """
        # retrieve file contents, if this fails the program exits anyway.
        if contents is None:
            contents = self.get_file_contents()

        # get text to find.
        finder = self.finder_text()

        # make sure the switch still exists.
        if self.is_regex():
            # regular expressions, find actual text to use for switch
            match = re.search(finder, contents)
            if match is None:
                print_fail(
                    'Switch {}\'s regular expression not found in: {}'.format(
                        self.get_name(),
                        self.filename))
            # get actual text from regex expression
            actualtext = match.group()
        else:
            # regular text will be used.
            if finder not in contents:
                print_fail('Switch {}\'s text not found in: {}'.format(
                    self.get_name(),
                    self.filename))
            actualtext = finder
        return actualtext

    def get_state(self, actual_value=False, contents=None):
        """ Retrieves current trigger state for this switch
            by reading its file and finding the current state.
            returns: 'on' or 'off' unless actual_value is True,
            then it returns whatever real value is found at the switch.
        """

        # Get file contents
        if contents is None:
            contents = self.get_file_contents()

        # Get switches actual text in the file
        actualtext = self.get_switch_text(contents)

        # find state
        splitter = contents.split(actualtext)
        if len(splitter) < 2:
            # nothing on the right side of the finder? someone messed up.
            print_fail(
                'Cannot find state for {} in: {}'.format(
                    self.get_name(),
                    self.filename))

        # state is everything up to the next comment or newline.
        rightside = splitter[1]
        # determine our stopping point.
        comment = rightside.index('#') if ('#' in rightside) else -1
        newline = rightside.index('\n') if ('\n' in rightside) else -1
        if (comment > -1) and (newline > -1) and (comment < newline):
            endchar = '#'
        elif (newline > -1):
            endchar = '\n'
        else:
            endchar = None

        # Find the end of the state (may be all of the state).
        if endchar is None:
            # Last line of the file, no comment after.
            state = rightside.strip(' ')
        else:
            # Get everything up to comment or newline.
            state = rightside[:rightside.index(endchar)].strip(' ')
        # remove = if needed.
        # (may have been included in the finder, though not needed)
        if '=' in state:
            state = state[state.index('=') + 1:].strip(' ')

        if actual_value:
            # just return the actual content of the value
            # (even if it doesn't match our acceptable values)
            return state
        else:
            # Return a verbose state (on or off)
            if self.is_version():
                # Versions have no verbose state.
                return state.strip('\'').strip('"')
            else:
                return 'on' if state == str(self.on_value()) else 'off'

    def get_switch_line(self, contents=None):
        """ Retrieves actual line of text that will be modified.
            (finder text = value)
            if contents is None, then contents are loaded.
        """

        # Get file contents
        if contents is None:
            contents = self.get_file_contents()

        # Get switch text
        actualtext = self.get_switch_text(contents)

        # find line
        splitter = contents.split(actualtext)
        if len(splitter) < 2:
            # nothing on right hand side?!
            print_fail(
                'Cannot find text line for {} in: {}'.format(
                    self.get_name(),
                    self.filename))

        if '\n' in splitter[1]:
            # state is everything up to next line.
            state = splitter[1][:splitter[1].index('\n')]
        else:
            # state is at the end of the file.
            state = splitter[1]

        # return whole line
        return actualtext + state

    def set_value(self, new_value, contents=None, dryrun=False):
        """ Sets the switch value in its file.
            if dryrun is True, no files will be modified. (for testing)
            you can pass file contents in if you want,
            otherwise they will be retrieved.
        """

        # Get file contents.
        if contents is None:
            contents = self.get_file_contents()

        # Get switch text.
        actualtext = self.get_switch_text(contents)
        # Get old actual value.
        oldvalue = self.get_state(True, contents)

        # Check version str increment.
        if self.is_version():
            verstr = oldvalue.strip('\'').strip('"')
            if new_value == '+':
                try:
                    new_value = '\'{}\''.format(increment_versionstr(verstr))
                except ValueError as ex:
                    print_fail('\nUnable to increment version string!\n'
                               '{}'.format(ex))
            else:
                print_fail('Version decrement not implemented yet!')

        # Regular switch, get new value to use.
        elif new_value.lower() in 'onoff':
            new_value = str(self.convert_value(new_value.lower()))
        else:
            print_fail('Invalid value for this switch!')

        # Cycle through lines of text.
        textlines = contents.split('\n')
        modified_lines = []
        for sline in textlines:
            # grab switch line.
            if actualtext in sline:
                # modify line.
                sline = sline.replace(oldvalue, new_value)
            # add to modified
            modified_lines.append(sline)

        filename = self.relative_filename()
        if dryrun:
            # just print the results to console.
            dividerlen = (80 - len(filename)) if len(filename) < 80 else 0
            print('\n' + self.relative_filename() + ':' +
                  ('-' * dividerlen) + '\n')
            print('\n'.join(modified_lines) + '\n' + ('-' * 80) + '\n')
        else:
            # modify file.
            try:
                with open(filename, 'w') as fwrite:
                    fwrite.write('\n'.join(modified_lines))
            except Exception as ex:
                print_fail(
                    'Error setting {} in: {}\nError: {}'.format(
                        self.get_name(),
                        self.filename,
                        ex))
        # Finished
        return new_value

    def relative_filename(self):
        """ Retrieves relative filename if we only have a short name. """
        if os.path.isfile(self.filename):
            return self.filename

        if '~' in self.filename:
            userpath = os.path.abspath(os.path.expanduser(self.filename))
            if os.path.isfile(userpath):
                return userpath

        if '..' in self.filename:
            abspath = os.path.abspath(self.filename)
            if os.path.isfile(abspath):
                return abspath

        shortname = os.path.split(self.filename)[-1]
        for checkpath in CHECK_DIRS:
            filename = os.path.join(checkpath, shortname)
            if os.path.isfile(filename):
                self.filename = filename
                return filename
        return None


class CmdlineExit(Exception):

    """ Error to raise when interactive cmd-line stuff is exited by user,
        this way I can trap it and handle it.
    """
    pass

# Global switches holder
switches = None
# char in between switch data
SWITCH_SEPARATOR = '|'
# Acceptable length of switch data when reading from file.
# read_file() will check len - 1 in case
# the description has been left out on purpose.
SWITCH_LEN = 5  # file|name|values|finder|description
# default switches list/file...
DEFAULT_SWITCHES_FILE = 'switches.conf'
# possible command-line switches for setting/getting switch values.
# When checking these args, '+' is appended if the switch is a version string.
good_switch_args = ['on', 'off', '-', '?', '!', '@']
# possible commands
good_commands = (
    'help', 'names', 'status', 'values',
    'full', 'groups', 'build', 'files')

# This can be overridden by the test module to make this quiet.
printerror = print


def main(args):
    """ main entry-point for wpswitches.
        expects args: ['switch_name',
                        'on' | 'off' | etc...,
                        possible other flags...]
    """
    global switches, DEFAULT_SWITCHES_FILE

    # help comes first.
    if args[0].lower() == 'help':
        print_help()
        sys.exit(0)
    elif args[0].lower() in ('-h', '--help'):
        print_usage()
        sys.exit(0)

    # Read switches file.
    DEFAULT_SWITCHES_FILE = find_file(DEFAULT_SWITCHES_FILE)
    if DEFAULT_SWITCHES_FILE:
        switches = read_file(DEFAULT_SWITCHES_FILE)
        if len(switches) == 0:
            print_fail('no switches are configured!\n'
                       'run \'wpswitch help\' for more info...')
    else:
        print_fail('no switches file found,\n'
                   'please put your switches in a local switches.conf...')

    # Check switches
    validate_switches()

    # Get arguments for switch name, value, and other args (flags)...
    name, val, other_args = validate_args(args)

    # Check flags
    bdryrun = (('-d' in other_args) or ('--dryrun' in other_args))
    brealvals = (('-r' in other_args) or ('--real' in other_args))

    if bdryrun:
        print('dry-run, no files will be modified!')

    # Commands ---------------------------------------
    if name.lower() in good_commands:
        do_command(name.lower(), val, dryrun=bdryrun)

    # Perform switch operations -----------------------
    if name.lower() in get_all_names():
        # Check switch value (on, off, or actual)
        if val in '!?':
            val = check_value(name, actual=(val == '!'))
        # Check switch text and value
        elif val == '@':
            val = check_line(name)
        # Set value/Toggle value
        elif val.lower() in 'onoff-+':
            sw = get_switch_byname(name)
            if sw.is_version() and val == '+':
                newval = '+'
            else:
                oppositeval = get_toggle_value(sw)

                if val == '-':
                    # Swap current value.
                    newval = oppositeval
                else:
                    # Check if its set already.
                    if val.lower() == oppositeval:
                        newval = val.lower()
                    else:
                        # Already set.
                        print_fail(
                            '{} is already set to: {}'.format(
                                sw.get_name(),
                                val.lower()))
            # Set new value
            setvalue = sw.set_value(newval, dryrun=bdryrun)
            if setvalue:
                # print results
                # (results double-check by grabbing actual value from file)
                if bdryrun:
                    showvalue = setvalue
                else:
                    showvalue = sw.get_state(actual_value=brealvals)

                results = '{} set to: {}'.format(sw.get_name(), showvalue)
                if bdryrun:
                    results += ' (not really)'
                print(results)
            else:
                print('\nUnable to set value [{}] for {}'.format(newval, name))
    else:
        print('\nNot a valid switch name: {}'.format(name.lower()))

    # Finished.
    sys.exit(0)


def check_value(name, actual=False):
    """ returns the value for a switch (on or off)
        if actual_value is True, then the actual code value is returned.
    """

    sw = get_switch_byname(name)
    if not sw:
        print_fail('\nCan\'t find that switch!: {}'.format(name))

    contents = sw.get_file_contents()

    actual_val = sw.get_state(True, contents)
    if sw.is_version():
        # Version strings have no 'state'.
        verbose_val = actual_val.strip('\'').strip('"')
    else:
        verbose_val = sw.convert_value(actual_val)
    # print to console.
    swname = sw.get_name()
    output = swname + ' : ' + verbose_val
    if actual:
        output += ' : ' + actual_val
    print(output + '\n')
    return verbose_val


def check_line(name):
    """ returns whole line. switch text + value """

    sw = get_switch_byname(name)
    contents = sw.get_file_contents()
    line = sw.get_switch_line(contents)
    state = sw.get_state(False, contents)
    # console output
    print(sw.get_name() + ': ' + state + '\n' + line)
    return line


def cmdline_build_switch(initial_name=None, dryrun=False, filename=None):
    """ interactive 'switch builder/editor' in the console,
        parses input to build a switch, validates info,
        and adds it to switches.conf.
    """
    if filename is None:
        filename = 'switches.conf'
    sw = get_switch_byname(initial_name)
    if sw is None:
        oldswitch = None
        sw = Switch()
        header = 'Ready to build switch: '
        if initial_name is not None:
            header += initial_name
        print(header + '\n')
    else:
        # save old switch for comparison during switch-write.
        oldswitch = copy.deepcopy(sw)
        print('Editing switch: {}\n'.format(sw.name))

    # prints prompts with current values (if any value is present)
    def prompt_val(s, val):
        max_prompt_len = 60
        if s.endswith(':'):
            s = s[0:-1]
        if val is None:
            s = s + ':'
        else:
            s = s + ' [' + str(val) + ']:'
        return (' ' * (max_prompt_len - len(s))) + s + ' '

    # Build list of current switch names to check against
    switch_names = [eachswitch.name for eachswitch in switches]
    # Include aliases in the switch names.
    for eachswitch in switches:
        if not eachswitch.aliases:
            continue
        switch_names.extend(eachswitch.aliases)

    # remove this name from the list if a name is set,
    # we will be using the list of names to block answers to the "name:"
    # prompt.
    if (sw.name is not None) and (sw.name in switch_names):
        switch_names.remove(sw.name)
    if (sw.aliases is not None):
        for thisalias in sw.aliases:
            if thisalias in switch_names:
                switch_names.remove(thisalias)

    try:
        # Build name, Aliases
        if initial_name is None:
            names = sw.name
        else:
            names = initial_name

        if sw.aliases is None:
            aliases = []
        else:
            names = ','.join(sw.aliases)
            aliases = sw.aliases

        name = cmdline_get_response(
            prompt_val('Name', names),
            default_value=names,
            blocked_values=switch_names)
        if ',' in name:
            # Set new aliases
            aliases += [a.strip(' ') for a in name.split(',')]
            name = aliases[0]
        else:
            if sw.aliases is not None:
                remove_aliases = cmdline_get_response(
                    prompt_val('Remove Aliases? (y/n)', 'n'),
                    acceptable_values=('y', 'n', 'yes', 'no'),
                    default_value='n',
                    allow_blank=False)
                if remove_aliases.startswith('y'):
                    aliases = []

        # remove duplicates from aliases.
        for aliasdupe in [a for a in aliases]:
            if aliases.count(aliasdupe) > 1:
                aliases.remove(aliasdupe)
        sw.name = name
        sw.aliases = None if aliases == [] else aliases

        # Group?
        group = cmdline_get_response(
            prompt_val('Group', str(sw.group)),
            default_value=str(sw.group),
            allow_blank=True)
        if group == '':
            group = None
        sw.group = group

        # Get filename
        sw.filename = cmdline_get_response(
            prompt_val('Target File', sw.filename),
            default_value=sw.filename,
            file_must_exist=True)

        # Get finder
        sw.finder = cmdline_get_response(
            prompt_val('Target String (Finder)', sw.finder),
            default_value=sw.finder)

        # Get Values
        if sw.values is None:
            onvalue = None
            offvalue = None
        else:
            onvalue = sw.values[0]
            offvalue = sw.values[1]

        onvalue = cmdline_get_response(
            prompt_val('On Value', onvalue),
            default_value=onvalue)
        offvalue = cmdline_get_response(
            prompt_val('Off Value', offvalue),
            default_value=offvalue)
        sw.values = (onvalue, offvalue)

        # Get Description
        sw.description = cmdline_get_response(
            prompt_val('Description', sw.description),
            default_value=sw.description,
            allow_blank=True)

        # Set values
        if sw == oldswitch:
            if dryrun:
                print(
                    '\nswitches are still equal,\nwould\'ve wrote: {}'.format(
                        sw.get_switch_str()))
            else:
                print('\nswitch not changed.')
        else:
            print('\nwriting switch: {}'.format(sw.get_name()))
            # if write_file(filename, dryrun):
            if write_switch_line(sw, oldswitch, filename, dryrun):
                print('...success.')

    except CmdlineExit:  # @UnusedVariable: excancel
        print('\nswitch editing cancelled, no changes were made.\n')


def cmdline_get_response(prompt, **kwargs):
    """ prints a prompt, retrieves response
        keyword arguments allow validation:
        allow_blank       : allow a blank answer
                            [default: False]
        default_value     : returns default value if answer is blank.
                            ** overrides allow_blank
                            [default: None]
        max_length        : maximum character length of answer
                            [default: 255]
        acceptable_values : list/tuple of acceptable answers
                             won't accept any other if given,
                             non-case-sensitive - no-spaces comparison made.
        blocked_values    : same as acceptable but reverse,
                            don't allow them as answers.
        file_must_exist   : response must be an existing file name/path
                            (full or relative)
                            [default: False]
        condition         : condition to check before allowing this answer
                            [default: True]
    """
    allow_blank = kwargs.get('allow_blank', False)
    default_value = kwargs.get('default_value', None)
    max_length = kwargs.get('max_length', 255)
    acceptable_values = kwargs.get('acceptable_values', None)
    blocked_values = kwargs.get('blocked_values', None)
    file_must_exist = kwargs.get('file_must_exist', False)
    condition = kwargs.get('condition', True)

    def answer_warn(s):
        print('\n'.join((
            '\n{}'.format(s),
            '...type !exit, !cancel, or !quit to cancel building this switch.',
            '')))

    # this traps the EOFError that is raised on user cancelling...
    # a CmdlineExit() is raised instead, same as when '!exit' is the response.
    # the calling function should trap CmdlineExit()...
    # (cmdline_build_switch())
    try:
        while True:
            response = input(prompt)
            response_trim = response.replace(' ', '').lower()
            response_multicheck = response_trim.replace(',', '')

            # first checks (exit, blank, max_len, acceptable answer)
            if (response_trim in ('!exit', '!cancel', '!quit')):
                raise CmdlineExit('User Cancelled')
            # Blank, use default value
            elif (response_trim == '' and (default_value is not None)):

                return default_value
            # Blank, no default, no blanks allowed
            elif (response_trim == '' and (not allow_blank)):
                answer_warn('You must provide an answer.')
            # All commas, weird, but would mess up the Name/Aliases prompt.
            elif (response_multicheck == '' and (not allow_blank)):
                answer_warn('\n'.join((
                    'Commas are for entering multiple values (where accepted)',
                    'but values cannot be empty.'
                )))
            # Max Length
            elif (len(response) > max_length):
                answer_warn(
                    'Answer was too long! > {} characters.'.format(max_length))
            # Acceptable Values
            elif (acceptable_values and
                  (response_trim not in acceptable_values)):
                acceptstr = '    {}'.format(
                    '\n    '.join(acceptable_values))
                acceptmsg = 'Has to be on of:\n{}'.format(acceptstr)
                answer_warn(
                    'Not an acceptable value.\n{}'.format(acceptmsg))
            # Blocked Values
            elif ((blocked_values is not None) and
                  (response_trim in blocked_values)):
                blockedstr = '\n    '.join(blocked_values)
                blockedmsg = 'Cannot be one of:\n{}'.format(blockedstr)
                answer_warn(
                    'Not an acceptable value.\n{}'.format(blockedmsg))
            # Must be a file that exists
            elif (file_must_exist and (not os.path.isfile(response))):
                answer_warn('File must exist (relative, or full path).')

            # All other checks passed
            else:
                # final check (condition)
                if condition:
                    return response

    except (EOFError, KeyboardInterrupt):
        raise CmdlineExit('User Cancelled')


def do_command(name, val, dryrun=False):
    """ perform a simple command and exit.
        name : the name of the command.
         val : any argument the command can accept
    """

    if (name != 'build') and (val is not None):
        group_members = get_group_members(val)
        if len(group_members) == 0:
            print_fail('no members found for group: {}'.format(val))

    if name == 'names':
        if val is None:
            list_switches()
        else:
            list_switches(group_members)
    elif name == 'status':
        if val is None:
            list_status(False)
        else:
            list_status(False, group_members)
    elif name == 'values':
        if val is None:
            list_status(True)
        else:
            list_status(True, group_members)
    elif name == 'full':
        if val is None:
            list_full()
        else:
            list_full(group_members)
    elif name == 'groups':
        list_groups()

    elif name == 'build':
        # start interactive switch builder
        cmdline_build_switch(val, dryrun)
    elif name == 'files':
        if val is None:
            list_files()
        else:
            list_files(group_members)

    sys.exit(0)


def find_file(filename):
    """ checks a couple of directories for a filename,
        returns the full path on success.
        returns False on failure.
    """

    if os.path.isfile(filename):
        return filename
    # check some directories for the file.
    for checkdir in CHECK_DIRS:
        # print('LOOKING IN: {} for {}'.format(checkdir, filename))
        possiblename = os.path.join(checkdir, filename)
        if os.path.isfile(possiblename):
            return possiblename
    return False


def find_unique_item(items):
    """ finds the first unique list/tuple item """

    trimmed_list = [i.replace(' ', '') for i in items]
    for i in range(0, len(trimmed_list)):
        item = trimmed_list[i]
        if trimmed_list.count(item) == 1:
            # return original item, not trimmed.
            return items[i]


def get_all_names(switch_list=None):
    """ Return a set of all switch names and aliases. """
    switch_list = switch_list or switches
    if switch_list is None:
        return []

    names = set()
    for sw in switch_list:
        if sw.aliases:
            names.update(sw.aliases)
        elif sw.name:
            names.add(sw.name)
    return names


def get_file_members(switch_list=None):
    """ returns all switches that use this filename as their target """

    if switch_list is None:
        switch_list = switches
    if switch_list is None:
        return {}
    results = {}
    for sw in switch_list:
        if sw.filename in results.keys():
            results[sw.filename].append(sw.name)
        else:
            results[sw.filename] = [sw.name]
    return results


def get_files(switch_list=None):
    """ returns a list of filenames belonging to switches. """

    if switch_list is None:
        switch_list = switches

    return list(set((sw.filename for sw in switch_list)))


def get_group_bylist(switchlist=None):
    """ determine the group from a list of switches.
        if all the groups aren't the same, returns "(mixed groups)"
    """

    if switchlist is None:
        switchlist = switches

    current_groups = list(set((sw.group for sw in switchlist)))

    if len(current_groups) > 1:
        list_group = '(mixed groups)'
    else:
        list_group = current_groups[0]

    return list_group


def get_group_members(groupname, switch_list=None):
    """ get all switches in a group.
        returns list of members.
    """

    if switch_list is None:
        switch_list = switches
    if groupname == '-' or groupname == '':
        groupname = 'None'

    members = []
    for sw in switch_list:
        if groupname.lower() == str(sw.group).lower():
            members.append(sw)
    return members


def get_groupname_from_line(line_):
    """ parses a groupname out of a single line in switches.conf,
        returned None on failure, or end of group "[/mygroup]".
        allows the same logic to be used everywhere switches are parsed from
        file.
    """
    line_ = strip_chars(line_, (' ', '\t', '\n'))
    # end of group.?
    if line_.startswith('['):
        if line_.startswith('[/'):
            groupname = None
        else:
            groupname = line_[1:-1]
    else:
        groupname = None
    return groupname


def get_groups(switch_list=None):
    """ returns a list of group names """
    if switch_list is None:
        switch_list = switches
    groups = []
    for sw in switch_list:
        if sw.group not in groups:
            groups.append(str(sw.group))
    return groups


def get_switch_byname(name, switch_list=None):
    """ retrieves switch by name """

    if not name:
        return None
    if not switch_list:
        switch_list = switches

    name = name.lower()

    for sw in switch_list:
        swname = sw.get_name()
        if swname and swname.lower() == name:
            return sw
        elif sw.aliases:
            if name in (a.lower() for a in sw.aliases):
                return sw

    return None


def get_toggle_value(name_or_switch):
    """ retrieves the opposite of whatever value the switch has.
        (what the switch should be toggled to)
    """

    if not isinstance(name_or_switch, (Switch)):
        name_or_switch = get_switch_byname(name_or_switch)
    oldval = name_or_switch.get_state()
    return 'off' if oldval == 'on' else 'on'


def increment_versionstr(s):
    """ Increments a version string, where s is
        is a version string in the form of:
        X.X.X
    """
    if not s.count('.') == 2:
        return s

    s = s.strip()

    def tryint(sint):
        try:
            val = int(sint)
        except:
            raise ValueError('Invalid integer in version string: '
                             '{}'.format(sint))
        return val

    def increment_ver(i):
        """ increment i, if it is > 9, return (i, True)
                otherwise, return (i, False).
        """
        i += 1
        return (0, True) if i > 9 else (i, False)

    major, minor, micro = [tryint(v) for v in s.split('.')]

    # We have a good version string, now increment it.
    micro, rolled = increment_ver(micro)
    if rolled:
        minor, rolled = increment_ver(minor)
    if rolled:
        # Major versions don't roll over.
        major += 1
    return '.'.join([str(v) for v in (major, minor, micro)])


def is_comment_line(line_):
    """ determines if a single line is a comment for switches config,
        allows the same logic to be used whereever switch parsing is done.
        unfortunately, this doesn't cover block comments with /* and */.
    """
    line_ = line_.replace(' ', '').replace('\t', '').replace('\n', '')
    return (
        line_.startswith('#') or
        line_.startswith('//') or
        line_.startswith(';'))


def list_full(switchlist=None):
    """ print a list of switch names and actual text lines """

    if switchlist is None:
        switchlist = switches
        s = 'current switch names and lines:'
    else:
        # Get group from switchlist passed.
        group = get_group_bylist(switchlist)
        s = 'current switch names and lines for group: {}'.format(group)
    print(s)

    for sw in switchlist:
        line = sw.get_switch_line()
        print('{}:\n{}\n'.format(sw.get_name(), line))


def list_groups():
    """ print group information """

    print('current groups:')
    # Get groups set by the user.
    groups = get_groups()
    # Add the 'None' group (where all non-grouped switches are.)
    groups.append('None')

    # Format for a switches info.
    grpfmt = '    {group}:'
    swtfmt = '        {name} : {state} ({actual})'
    for group in groups:
        displayname = '(no group)' if group == 'None' else group
        print(grpfmt.format(group=displayname))

        for sw in get_group_members(group):
            contents = sw.get_file_contents()
            swtfmtargs = {
                'name': sw.name.ljust(10),
                'state': sw.get_state(False, contents),
                'actual': sw.get_state(True, contents)
            }
            print(swtfmt.format(**swtfmtargs))


def list_files():
    """ print all filenames for switches. """

    filemembers = get_file_members()

    print('file members:')
    if len(filemembers) == 0:
        print('    (no switches)\n')
    else:
        for filename in filemembers.keys():
            print('    {}:'.format(filename))
            print('        {}\n'.format(
                '\n        '.join(filemembers[filename])))


def list_status(full_value=False, switchlist=None):
    """ print a list of switch names and states """

    if switchlist is None:
        switchlist = switches
        s = 'current switch names and states:'
    else:
        group = get_group_bylist(switchlist)
        s = 'current switch names and states for group: {}'.format(group)
    print(s)

    for sw in switchlist:
        contents = sw.get_file_contents()
        status = '{} : {}'.format(
            sw.get_name().rjust(15),
            sw.get_state(False, contents))
        # Show actual value, unless its a version string.
        if full_value and not sw.is_version():
            status = '{} ({})'.format(
                status,
                sw.get_state(True, contents))
        print(status)


def list_switches(switchlist=None):
    """ print a list of current switches """

    if switchlist is None:
        switchlist = switches
        s = 'current switch names:'
    else:
        group = get_group_bylist(switchlist)
        s = 'current switch names for group: {}'.format(group)
    print(s)
    for sw in switchlist:
        print('    {}'.format(sw.get_name()))


def parse_switchdata(switchline):
    """ retrieves individual items from switchdata text line.
        this works on a single line only, parsing whole files is done with
        read_file().
        ex:
            myswitch = parse_switchdata(
                "setting.py|name|on_val,off_val|FINDER_TEXT|description")
        returns None on failure.
    """
    switchline = strip_chars(switchline, (' ', '\t', '\n', '|'))
    # may contain an empty value, this would break everything.
    if '||' in switchline:
        return None

    switchdata = switchline.split('|')
    data_len = len(switchdata)
    skip = False
    if (data_len < SWITCH_LEN - 1) or (data_len > SWITCH_LEN):
        printerror((
            '\nbad switch data, wrong item length: {}').format(switchline))
        sw_file = name = values = finder = desc = None
        skip = True
    else:
        # parse switch data
        sw_file = switchdata[0].strip(' ').strip('\t')
        if sw_file.startswith('|'):
            sw_file = sw_file[1:]
        # name
        name = switchdata[1]
        # has aliases?
        if ',' in name:
            name = [n.strip(' ') for n in name.split(',')]
        # possible values.
        values = parse_values(switchdata[2])
        # error parsing values?
        if hasattr(values, 'encode'):
            printerror('{}{}'.format(values, switchline))
            skip = True

        # finder text
        finder = switchdata[3]
        if finder.endswith(SWITCH_SEPARATOR) or finder.endswith('\n'):
            finder = finder[:-1]
            desc = None

        # possible description
        desc = None
        if len(switchdata) > 4:
            desc = switchdata[4]
            if desc.endswith(SWITCH_SEPARATOR) or desc.endswith('\n'):
                desc = desc[:-1]
            if len(desc) == 0:
                desc = None
        newswitch = None if skip else Switch(
            sw_file, name, values, finder, desc)
        return newswitch


def parse_values(values):
    """ retrieve a list of two values from a values string (value1, value2).
        handles lists/tuples/quotes/etc.
        returns values list of 2 items on success.
        returns error string on failure.
    """
    if ',' in values:
        # reg ex for finding proper value separator.
        # some times a comma is needed for proper values (lists, tuples, dicts,
        # quoted strings)
        sep_pattern = re.compile(
            '["\'\\}\\]\\)][ ]{0,50},[ ]{0,50}["\'\\{\\[\\(]')
        sep_find = sep_pattern.findall(values)

        # determine separator
        if len(sep_find) == 0:
            # simple comma
            value_sep = ','
            val1_end = val2_start = ''
        else:
            # special char separators
            if len(sep_find) == 1:
                # easy list/tuple with quoted items separator found.
                value_sep = sep_find[0]
            else:
                # quoted items within list/tuple values. find the actual
                # separator
                value_sep = find_unique_item(sep_find)
                # print_debug("UNIQUE ITEM: " + value_sep)
            # chars to fill in missing pieces because of regex separator search
            # result
            val2_start = value_sep.replace(' ', '')[-1]
            val1_end = value_sep.replace(' ', '')[0]

        values = [v.strip(' ') for v in values.split(value_sep)]

        if len(values) != 2:
            values = '\nbad switch data, too many possible values: '
        else:
            # fix missing start/end from regex.
            values[0] = values[0] + val1_end
            values[1] = val2_start + values[1]

    else:
        values = '\nbad switch data, not enough possible values: '

    return values


def print_block(msgitems, singlevalue=None):
    """ Print key: value style messages. """
    if singlevalue:
        print('{:>4}: {}'.format(msgitems, singlevalue))
        return None

    maxlen = len(max((k for k, _ in msgitems), key=len))
    indent = ' ' * maxlen
    for k, v in msgitems:
        if isinstance(v, (list, tuple)):
            print('{}{}'.format(k.rjust(maxlen), v[0]))
            for subval in v[1:]:
                print('{}{}'.format(indent, subval))
        else:
            print('{}{}'.format(k.rjust(maxlen), v))


def print_debug(*args, **kwargs):
    """ just a wrapper for print that can be easily searched for and replaced.
    """
    print(*args, **kwargs)


def print_fail(sreason=None):
    """ exits the script, with a reason given if needed. """

    if sreason is not None:
        print(sreason)
    print('\nGoodbye.\n')
    sys.exit(1)


def print_help():
    """ print a long message about how to configure and use wpswitch """
    print(help_str)


def print_usage(sreason=None):
    """ prints usage, with a reason for showing it if needed """
    if sreason is not None:
        print(sreason)

    print(usage_str)


def read_file(filename='switches.conf'):
    """ reads a set of switches from a file. """

    filepath = find_file(filename)
    if not filepath:
        print_fail('switches file does not exist!: {}'.format(filename))
    try:
        with open(filepath) as fread:
            lines = fread.readlines()
    except Exception as ex:
        print_fail('unable to read file: {}\n{}'.format(filepath, ex))
    return read_lines(lines)


def read_lines(lines):
    """ reads a set of switches from a list of strings,
        like: good_switches = read_lines(open('myfile.txt').readlines())
        returns a list of switches.
    """
    good_switches = []
    incommentblock = False
    groupline = False
    groupname = None

    for switchline in lines:
        switchline = strip_chars(switchline, (' ', '\t', '\n', '|'))

        trimmedline = switchline.replace(
            ' ', '').replace('\t', '').replace('\n', '')
        commentline = is_comment_line(trimmedline)

        groupline = trimmedline.startswith('[')

        # Start of comment block.
        if trimmedline.startswith('/*'):
            incommentblock = True
        # Group
        elif groupline:
            newgroupname = get_groupname_from_line(trimmedline)
            if newgroupname is not None:
                groupname = newgroupname
        # Start of switch data
        # (not a comment/group declaration, has data separators...)
        if ((not incommentblock) and (not commentline) and (not groupline) and
                (SWITCH_SEPARATOR in switchline)):
            # Actual switch data.
            newswitch = parse_switchdata(switchline)
            newswitch.group = groupname
            # Build switch.
            if newswitch is None:
                print('skipping switch: {}'.format(switchline))
            else:
                good_switches.append(newswitch)

        # End of comment block
        if trimmedline.endswith('*/'):
            incommentblock = False

    # finished.
    return good_switches


def strip_chars(str_, char_list=None):
    """ strips all characters in the list using strip() """

    if char_list is None:
        char_list = (' ', '\t', '\n')

    for ch in char_list:
        str_ = str_.strip(ch)
    return str_


def validate_args(args):
    """ makes sure valid arguments are passed. """

    name = args[0]
    is_command = (name.lower() in good_commands)

    if len(args) < 2:
        if not is_command:
            print_usage('Missing argument!')
            sys.exit(1)
        # commands won't use these (yet)
        other_args = []
        val = None
    elif len(args) == 2:
        other_args = []
        val = args[1]
    else:
        other_args = args[2:]
        val = args[1]

    if not is_command:
        # check switch name
        sw = get_switch_byname(name)

        if sw is None:
            print_fail('switch/command not found: {}'.format(name))
        # check possible values
        if sw.is_version():
            good_switch_args.append('+')
        if not val.lower() in good_switch_args:
            print_usage((
                'Bad switch value!: {}\nExpecting: {}'
            ).format(val, ', '.join(good_switch_args)))
            sys.exit(1)

    # return arguments as: (name, value, (all other args, or empty list))
    return [name, val, other_args]


def validate_switches():
    """ make sure switches aren't duplicates,
        and groups don't have the same name as switches.
    """

    if switches is None:
        print_fail('\n'.join((
            'no switches to validate!',
            'run \'wpswitch help\' for more info...')))

    switch_names = []
    for sw in switches:
        if sw.aliases is None:
            switch_names.append(sw.get_name())
        else:
            # get alias names
            for alias in sw.aliases:
                switch_names.append(alias)

    group_names = get_groups()

    duplicate_switches = []
    switch_group_conflicts = []

    for switch_name in switch_names:
        if switch_names.count(switch_name) > 1:
            if switch_name not in duplicate_switches:
                duplicate_switches.append(switch_name)
        if switch_name in group_names:
            if switch_name not in switch_group_conflicts:
                switch_group_conflicts.append(switch_name)

    err_count = len(duplicate_switches + switch_group_conflicts)
    if err_count > 0:
        if len(duplicate_switches) > 0:
            print('duplicate switch names found!:')
            for dupe_switch in duplicate_switches:
                print('    {}'.format(dupe_switch))
        if len(switch_group_conflicts) > 0:
            print('conflicting switch and group names found!:')
            for conflict in switch_group_conflicts:
                print('    {}'.format(conflict))
        print('\n'.join((
            '\nswitch config errors found: {}'.format(err_count),
            'please correct these errors and try again.'
        )))
        sys.exit(1)


def write_file(filename='switches.conf', dryrun=False):
    """ Writes all switches to file.
        Warning: This will overwrite the existing switches.conf.
                 All comments will be replaced, and switches will be
                 re-ordered (groups will be correct).
    """

    filepath = find_file(filename)
    if not filepath:
        filepath = filename
        print('\nfile not found, trying to create a new one: {}'.format(
            filepath))

    newcontents = []
    for groupname in get_groups():
        newcontents.append('[{}]\n'.format(groupname))
        groupswitches = get_group_members(groupname)
        linesstr = '\n    '.join([sw.get_switch_str() for sw in groupswitches])
        newcontents.append('    {}'.format(linesstr))
        newcontents.append('\n[\\{}]\n'.format(groupname))

    if dryrun:
        print('\nwriting file: {}\n\n'.format(filepath))
        print(''.join(newcontents))
        return True
    else:
        try:
            with open(filepath, 'w') as fwrite:
                fwrite.writelines(newcontents)
                return True
        except (OSError, IOError) as exio:
            print_fail(
                'unable to write switches file: {}\n{}'.format(
                    filepath,
                    exio))
        except Exception as ex:
            print_fail(
                'error writing switches file: {}\n{}'.format(
                    filepath,
                    ex))
    return False


def write_switch_line(
        switch_, prev_switch=None, filename='switches.conf', dryrun=False):
    """ Replace an old switch line with a new one in switches.conf,
        If prev_switch is not passed, the new one is simply added to the end.
        * switch_ must be a valid Switch().
    """

    filepath = find_file(filename)
    if not filepath:
        print_fail('switches file does not exist!: '.format(filename))

    try:
        oldlines = []
        with open(filepath) as fread:
            oldlines = fread.readlines()
    except (OSError, IOError) as exio:
        print_fail(
            'unable to read file for editing: '.format(
                filename,
                exio))
    except Exception as ex:
        print_fail(
            'error reading file for edit: {}\n{}'.format(
                filename,
                ex))

    switchstr = switch_.get_switch_str()

    editedlines = []
    commentblock = False
    replaced = False
    for oldline in oldlines:
        # line will not be changed unless it needs
        # to be replaced by the new one.
        editedline = oldline
        oldtrim = strip_chars(oldline, (' ', '\t', '\n'))

        # start of comment block?
        if oldtrim.startswith('/*'):
            commentblock = True
        # empty line?
        emptyline = (oldtrim == '')
        # comment line?
        commentline = (is_comment_line(oldline) or commentblock)
        # group line?
        groupline = oldtrim.startswith('[')
        if groupline:
            groupname = get_groupname_from_line(oldtrim)

        # This is switch data.
        if (not commentline) and (not groupline) and (not emptyline):
            # get current line's Switch()
            oldswitch = parse_switchdata(oldline)

            # is this the switch to be replaced?
            switchexists = (
                oldswitch and (oldswitch.get_name() == switch_.get_name()))
            # was there a previous switch by this name?
            replaceprev = (
                prev_switch and
                (oldswitch.get_name() == prev_switch.get_name()))
            if (switchexists and replaceprev):
                # warn about changing groups (for now)
                if prev_switch.group != switch_.group:
                    oldgroup = str(prev_switch.group)
                    newgroup = str(switch_.group)
                    print('\n')
                    warnmsg = (
                        ('** warning: ', (
                            'group has changed from \'{}\' to \'{}\'.'.format(
                                oldgroup,
                                newgroup),
                            'this switch is being placed in \'{}\'.'.format(
                                groupname))
                         ),
                    )
                    print_block(warnmsg)

                # Replace old switch setting.
                editedline = oldline.replace(oldtrim, switchstr)
                if dryrun:
                    print('\n')
                    print_block((
                        ('replacing old switch: ', oldtrim),
                        ('with: ', switchstr)
                    ))

                replaced = True

        # add the line (edited or not)
        editedlines.append(editedline)
        # end of comment block?
        if oldtrim.endswith('*/'):
            commentblock = False

    # Add as new switch
    if not replaced:
        if dryrun:
            print('\nadding new line:\n    {}'.format(switchstr))
        editedlines.append(switchstr)

    # Write new file
    if dryrun:
        print('\n\nwriting file {}...'.format(filename))
        print(''.join(editedlines))
    else:
        try:
            with open(filepath, 'w') as fwrite:
                fwrite.writelines(editedlines)
        except (OSError, IOError) as exio:
            print_fail('unable to write file for editing: {}\n{}'.format(
                filename,
                ex))
        except Exception as ex:
            print_fail('error writing file for edit: {}\n{}'.format(
                filename,
                ex))

    return True


# START OF SCRIPT -------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage('No arguments given!')
        sys.exit(1)

    main(sys.argv[1:])
