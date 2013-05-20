#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Switches
     @summary: Turns features/settings on or off by replacing code or variable values.
               Meant to be single file executable, hopefully it doesn't get too messy.
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 2, 2013
'''

import copy # copies switch() class, saves previous version while editing/building switches.
import sys
import os.path
import re # for regex 'finders'

usage_str = """
    usage: wpswitch <command> | <switch_name on|off|-|?|!|@> [options]
    
    commands:
              help : show the long help message
         -h,--help : show the usage help message
             names : list all switch names
            groups : list all groups and members
            status : list all switch names and state
            values : list all switch names and actual values
              full : list all switch names and actual lines

    switch operations:
                on : turn this switch on
               off : turn this switch off
                 - : toggle it's current state
                 ? : show it's current state (on|off)
                 ! : show it's actual code value
                 @ : show switches full text and value
    
    options:
      -d, --dryrun : dry run, don't modify any files (will print to console)
        -r, --real : show the real value when setting switches. 
        
    """

help_str = """
    wpswitch help:
    
    what is this?:
        wpswitch can modify/switch between two values for a single variable from the 
        command line. you need to tell it what to look for, where to find it, and
        what the two possible values are. once the switches are configured,
        changing between debug and live mode in django is as easy as typing:
        wpswitch debug on
        or, toggling it's current state with:
        wpswitch debug -
    
    how it works:  
        what's going on is wpswitch is looking in your switches for one named
        'debug', reading the file that you've assigned this switch to, and grabbing
        it's value. once the current value is known its just a simple text replace.
        when you run 'wpswitch debug on', it looks for what 'on' means for a switch
        called 'debug'. in this case 'on' means 'True'. the 'debug' switch's 'finder'
        would be set to 'DEBUG =' or 'TEMPLATE_DEBUG = DEBUG =', this tells wpswitch
        what this switch is, so it can find it and switch between it's configured 'on' 
        and 'off' values.
    
    how to make a switch:
        create a file called "switches.conf" in the same directory as this script.
        in that file, each line will be a switch.
        (except for comments, i will explain later).
        the switch data line should look like this:
        
        filename|name,or several names|on value,off value|finder|description
        or:
        filename|name,name2,name3|on_value,off_value|regex_finder
        * in this one the description has been left out on purpose.
        
            filename: the file containing this switch/finder.
                      must be a full path or relative to the location of this script.
                name: the name of the switch. 
                      this can be a comma-separated list of aliases so the same switch 
                      can be called by different names.
        on,off value: two values with a comma between them. the first is what 'on' means,
                      the second is what 'off' means.
              finder: how to find this switch. it can be plain text, or a regular expression.
                      if a regex is used, it must start and end with / like: /regex+goes+here/
         description: just a short comment/description about this switch, or empty.
         
         example switch for simple django debug setting:
             /mydir/myapp/settings.py|debug|True,False|DEBUG =|toggle debug mode
             * notice the = sign, this ensures that only a line with DEBUG = gets replaced.
             * without it, the word DEBUG (case-sensative) would be replaced everywhere in 
               the file.
            ** be careful with your finders! make sure the variable is uniquely named and can 
               be found easily by the finder.
         
         example switch with 3 possible names for changing port numbers:
             /mydir/settings.py|port,portnum,p|2600,81|myportvariable|switch ports
             * this switch can now be turned on with: wpswitch port on, wpswitch portnum on, 
               or wpswitch p on
            
         example switch using regex for the finder:
             settings.py|database,db|PSQL_DB,TEST_DB|/DEFAULT_D(ATA)?B(ASE)?/|switch prod. and test db
             * this would switch a variable named DEFAULT_DB or DEFAULT_DATABASE to the configured on 
               or off values.
             * make sure your regex only matches a single variable/switch! otherwise it will not 
               work correctly.
             * in this example the default database being used is switched by changing DEFAULT_DB's 
               value to one of two preset variables, PSQL_DB or TEST_DB.
         
         comments:
             the switch configuration does several types of commenting. comments may not be on the 
             same line as switch lines. you can start a line with "#" or "//" with or without 
             spaces/tabs preceding it, or you can do a block style comment using /* to start 
             and */ to end.
             example comments:
                 # this would work
                 // this would also work
                 /* this
                     would
                      work
                       also */
                 myfile.txt|myswitch|1,0|myuniquevariablename|example #this would not!
                 myfile2.txt|myswitch2|1,0|myuniquevariablename2|example #2 would be in the desc.
        
        notes:
            there are many ways to accomplish what this script does. things like 'awk' and 'sed' 
            come to mind. this script was designed for a very specific purpose, and does only 
            what i needed it to do and nothing else. it was meant to be extendable and easily 
            accessable. some times i don't want to use a terminal editor to change my website 
            settings. i like to edit offline on my own machine. some times it would take longer 
            to open the file, scroll to the line, edit, and save the changes. 
            
            running something like 'wpswitch testdatabase off' seems a lot better to me.
    """
             
        
        
        
# Switch Class
class switch(object):
    """ Holds info about a single switch, 
        such as Name, Possible Values for On/Off,
        and the RegEx/Text needed to find the switch. """
        
    def __init__(self, filename=None, name=None, default_values=None, finder=None, description=None, group=None):
        """       Filename: File where we can find the switch (the finder text).
                            Must be in same directory, or relative path of same directory.
                            ex: settings_local.py -or- /main/settings.py
                      Name: Name of switch
                            ex: "debug"
            Default Values: List/Tuple of values for On and Off. (OnValue, OffValue)
                            ex: (True, False)
                    Finder: Text to find this switch, if it starts with and ends with /, it's regex.
                            ex: "DEBUG = " (works better on single line, otherwise may break.)
                            ** Regex should only match a single switch! 
                               multiple matching switches won't work!
               Description: A comment, or description about this switch.
                     Group: Name of the group this switch belongs to, or None if not grouped.
        """
        
        
        self.filename = filename
        # allows setting multiple names for a switch ["database", "db"]
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
    
    def __unicode__(self):
        """ unicode representation of switch """
        
        return unicode(self.name, encoding='utf-8')
    
    def __repr__(self):
        """ representation of switch """
        return self.get_switch_str()
    
    def __eq__(self, other):
        if isinstance(other, switch):
            return ((self.get_switch_str() == other.get_switch_str()) and (self.group == other.group))
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
            values = 'None'
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
            return self.name
        else:
            return self.aliases[0]
        
    
    def get_description(self):
        """ safely retrieves a description (returns 'None' string on failure) """
        
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
            example where sw = switch(): 
                actual = self.convert_value(sw.get_state())
            ...if you wanted the actual value, not the converted actual value,
               you could just do this: actual_really = sw.get_state(actual_value=True)
            possible_values may not be a string.
        """
        
        possible_values = {"on":self.on_value(),
                           "off":self.off_value()}
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
            print_fail("Cannot find file for " + str(self.get_name()) + ': ' + self.filename)

        try:
            with open(filename) as fread:
                contents = fread.read()
        except Exception as ex:
            print_fail("Cannot retrieve contents for " + self.get_name() + " : " + self.filename + '\n' + \
                       "Error: " + str(ex))
        # everything passed, return contents.
        return contents
    
    def get_switch_text(self, contents = None):
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
            match_ = re.search(finder, contents)
            if match_ is None:
                print_fail("Switch " + self.get_name() + \
                           "'s regular expression not found in: " + self.filename)
            # get actual text from regex expression
            actualtext = match_.group()
        else:
            # regular text will be used.
            if not finder in contents:
                print_fail("Switch " + self.get_name() + \
                           "'s text not found in: " + self.filename)
            actualtext = finder
        return actualtext
    
    def get_state(self, actual_value = False, contents=None):
        """ Retrieves current trigger state for this switch
            by reading its file and finding the current state.
            returns: "on" or "off" unless actual_value is True,
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
            print_fail("Cannot find state for " + self.get_name() + \
                        " in " + self.filename + "!")

        # state is everything up to the next comment or newline.
        rightside = splitter[1]
        # determine our stopping point.
        comment = rightside.index("#") if ("#" in rightside) else -1
        newline = rightside.index('\n') if ("\n" in rightside) else -1
        if (comment > -1) and (newline > -1) and (comment < newline):
            endchar = "#"
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
        # remove = if needed. (may have been included in the finder, though not needed)
        if "=" in state:
            state = state[state.index("=") + 1:].strip(' ')

        if actual_value:
            # just return the actual content of the value 
            # (even if it doesn't match our acceptable values)
            return state
        else:
            # Return a verbose state (on or off)
            return "on" if state == str(self.on_value()) else "off"
                
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
            print_fail("Cannot find text line for " + self.get_name() + \
                       " in " + self.filename + "!")
        
        if '\n' in splitter[1]:
            # state is everything up to next line.
            state = splitter[1][:splitter[1].index('\n')]
        else:
            # state is at the end of the file.
            state = splitter[1]
            
        # return whole line
        return actualtext + state
    
    def set_value(self, new_value, contents = None, dryrun = False):
        """ Sets the switch value in its file.
            if dryrun is True, no files will be modified. (for testing)
            you can pass file contents in if you want,
            otherwise they will be retrieved.
        """
        
        # Get actual new value to use.
        if new_value.lower() in "onoff":
            new_value = str(self.convert_value(new_value.lower()))
        
        # Get file contents.
        if contents is None:
            contents = self.get_file_contents()
        
        # Get switch text.
        actualtext = self.get_switch_text(contents)
        # Get old actual value.
        oldvalue = self.get_state(True, contents)
        
        # Cycle through lines of text.
        if '\n' in contents:
            textlines = contents.split('\n')
        else:
            textlines = [contents]
        
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
            print '\n' + self.relative_filename() + ':' + ('-' * dividerlen) + "\n"
            print '\n'.join(modified_lines) + '\n' + ('-' * 80) + '\n'
        else:
            # modify file.
            try:
                with open(filename, 'w') as fwrite:
                    fwrite.write('\n'.join(modified_lines))
            except Exception as ex:
                print_fail("Error setting " + self.get_name() + \
                           " in " + self.filename + "!\n" + \
                           str(ex))
        # Finished
        return True
           
    def relative_filename(self):
        """ Retrieves relative filename if we only have a short name. """
        
        if os.path.isfile(self.filename):
            return self.filename
        elif os.path.isfile(os.path.join(sys.path[0], self.filename)):
            return os.path.join(sys.path[0]. self.filename)
        else:
            return None

class cmdlineExit(Exception):
    """ Error to raise when interactive cmd-line stuff is exited by user,
        this way I can trap it and handle it.
    """
    pass

# Global switches holder
switches = None
# char in between switch data
SWITCH_SEPARATOR = '|'
# Acceptable length of switch data when reading from file.
# read_file() will check len - 1 in case the description has been left out on purpose.
SWITCH_LEN = 5 # file|name|values|finder|description
# default switches list/file...
DEFAULT_SWITCHES_FILE = "switches.conf"
# possible command-line switches for setting/getting switch values.
good_switch_args = ("on", "off", "-", "?", "!", "@")
# possible commands
good_commands = ("help", "names", "status", "values", "full", "groups", "build")

def main(args):
    """ main entry-point for wpswitches.
        expects args: ["switch_name", 
                        "on" | "off" | etc..., 
                        possible other flags...]
    """
    global switches
    
    # help comes first.
    if args[0].lower() == "help":
        print_help()
        sys.exit(0)
    elif args[0].lower() == "-h" or args[0].lower() == '--help':
        print_usage()
        sys.exit(0)
    
    # Read switches file.
    if os.path.isfile(DEFAULT_SWITCHES_FILE):
        switches = read_file(DEFAULT_SWITCHES_FILE)
        if len(switches) == 0:
            print_fail("no switches are configured!\nrun 'wpswitch help' for more info...")
    else:
        print "using default built-in switches."
    
    # Check switches
    validate_switches()
       
    # Get arguments for switch name, value, and other args (flags)...
    name, val, other_args = validate_args(args)
    
    # Check flags
    bdryrun = (("-d" in other_args) or ("--dryrun" in other_args))
    brealvals = (("-r" in other_args) or ("--real" in other_args))
    
    if bdryrun:
        print "dry-run, no files will be modified!"
    

            
    # Commands ---------------------------------------
    if name.lower() in good_commands:
        do_command(name.lower(), val, dryrun=bdryrun)
 
    # Perform switch operations -----------------------
    if name.lower() in [sw.name.lower() for sw in switches]:
        # Check switch value (on, off, or actual)
        if val in "!?":
            val = check_value(name, actual=(val == "!"))
        # Check switch text and value
        elif val == "@":
            val = check_line(name)
        # Set value/Toggle value
        elif val.lower() in "onoff-":
            sw = get_switch_byname(name)
            oppositeval = get_toggle_value(sw)
            
            if val == "-":
                # Swap current value.
                newval = oppositeval
            else:
                # Check if its set already.
                if val.lower() == oppositeval:
                    newval = val.lower()
                else:
                    # Already set.
                    print_fail(sw.get_name() + " is already set to: " + val.lower())
            # Set new value
            if sw.set_value(newval, dryrun = bdryrun):
                # print results (results double-check by grabbing actual value from file)
                results = sw.get_name() + " set to: " + sw.get_state(actual_value=brealvals)
                if bdryrun:
                    results += " (not really)"
                print results
                
    # Finished.
    sys.exit(0)
    

def do_command(name, val, dryrun=False):
    """ perform a simple command and exit. 
        name : the name of the command.
         val : any argument the command can accept
    """
    
    if (name != "build") and (val is not None):
        group_members = get_group_members(val)
        if len(group_members) == 0:
            print_fail("no members found for group: " + val)
    
    if name == "names":
        if val is None:
            list_switches()
        else:
            list_switches(group_members)
    elif name == "status":
        if val is None:
            list_status(False)
        else:
            list_status(False, group_members)
    elif name == "values":
        if val is None:
            list_status(True)
        else:
            list_status(True, group_members)
    elif name == "full":
        if val is None:
            list_full()
        else:
            list_full(group_members)
    elif name == "groups":
        list_groups()
        
    elif name == "build":
        # start interactive switch builder
        cmdline_build_switch(val, dryrun)
        
    sys.exit(0)

def check_value(name, actual=False):
    """ returns the value for a switch (on or off)
        if actual_value is True, then the actual code value is returned.
    """
    
    sw = get_switch_byname(name)
    contents = sw.get_file_contents()
    
    actual_val = sw.get_state(True, contents)
    verbose_val = sw.convert_value(actual_val)
    # print to console.
    output = sw.get_name() + " : " + verbose_val
    if actual:
        output += " : " + actual_val
    print output + '\n'
    return verbose_val


def check_line(name):
    """ returns whole line. switch text + value """
    
    sw = get_switch_byname(name)
    contents = sw.get_file_contents()
    line = sw.get_switch_line(contents)
    state = sw.get_state(False, contents)
    # console output
    print sw.get_name() + ': ' + state + '\n' + line
    return line


def list_switches(switchlist = None):
    """ print a list of current switches """
    
    if switchlist is None:
        switchlist = switches
        s = "current switch names:"
    else:
        group = get_group_bylist(switchlist)
        s = "current switch names for group: " + group
    print s
    for sw in switchlist:
        print "    " + sw.get_name()


def list_status(full_value = False, switchlist=None):
    """ print a list of switch names and states """
    
    if switchlist is None:
        switchlist = switches
        s = "current switch names and states:"
    else:
        group = get_group_bylist(switchlist)
        s = 'current switch names and states for group: ' + group
    print s
    
    for sw in switchlist:
        contents = sw.get_file_contents()
        status = "    " + sw.get_name() + " : " + sw.get_state(False, contents)
        if full_value:
            status += " (" + sw.get_state(True, contents) + ")"
        print status
        

def list_full(switchlist=None):
    """ print a list of switch names and actual text lines """
    
    if switchlist is None:
        switchlist = switches
        s = "current switch names and lines:"
    else:
        # Get group from switchlist passed.
        group = get_group_bylist(switchlist)
        s = 'current switch names and lines for group: ' + group
    print s
    
    for sw in switchlist:
        line = sw.get_switch_line()
        print sw.get_name() + ":\n" + line + '\n'
    

def list_groups():
    """ print group information """
    
    print "current groups:"
    groups = get_groups()
    # add the 'None' group.
    groups.append('None')
    
    # print'em
    for group in groups:
        displayname = '(no group)' if group == 'None' else group
        print '    ' + displayname + ": "
        for sw in get_group_members(group):
            contents = sw.get_file_contents()
            print '        ' + sw.name + " : " + sw.get_state(False, contents) + ' (' + sw.get_state(True, contents) + ')'
            

def get_groups(switch_list=None):
    """ returns a list of group names """
    if switch_list is None: switch_list = switches
    groups = []
    for sw in switch_list:
        if not sw.group in groups: groups.append(str(sw.group))
    return groups
    

def get_group_members(groupname, switch_list=None):
    """ get all switches in a group.
        returns list of members.
    """
    
    if switch_list is None: switch_list = switches
    if groupname == '-' or groupname == '':
        groupname = 'None'
        
    members = []
    for sw in switch_list:
        if groupname.lower() == str(sw.group).lower():
            members.append(sw)
    return members


def get_group_bylist(switchlist = None):
    """ determine the group from a list of switches.
        if all the groups aren't the same, returns "(mixed groups)"
    """
    
    if switchlist is None:
        switchlist = switches
    
    current_groups = []
    for group in [sw.group for sw in switchlist]:
        if not group in current_groups:
            current_groups.append(str(group))
    
    if len(current_groups) > 1:
        list_group = '(mixed groups)'
    else:
        list_group = current_groups[0]
    
    return list_group
        
def get_switch_byname(name, switch_list=None):
    """ retrieves switch by name """
    
    if name is None: return None
    if switch_list is None: switch_list = switches
    
    for sw in switch_list:
        if sw.aliases is None:
            # Check against single name
            swname = sw.get_name()
            if swname is not None:
                if swname.lower() == name.lower():
                    return sw
        else:
            # Check all aliases
            for alias in [a.lower() for a in sw.aliases]:
                if alias == name.lower():
                    return sw
    return None


def get_toggle_value(name_or_switch):
    """ retrieves the opposite of whatever value the switch has.
        (what the switch should be toggled to)
    """
    
    if not isinstance(name_or_switch, (switch)):
        name_or_switch = get_switch_byname(name_or_switch)
    oldval = name_or_switch.get_state()
    return "off" if oldval == "on" else "on"


def file_exists(filename="switches.conf"):
    """ checks filepath, or current directory for file. """
    
    if not os.path.isfile(filename):
        filename = os.path.join(sys.path[0], filename)
        if not os.path.isfile(filename):
            return False
    return filename

def read_file(filename="switches.conf"):
    """ reads a set of switches from a file. """
    
    filepath = file_exists(filename)
    if not filepath:
        print_fail("switches file does not exist!: " + filename)
    
    try:
        with open(filepath) as fread:
            lines = fread.readlines()
    except Exception as ex:
        print_fail("unable to read file: " + filepath + '\n' + \
                   str(ex))
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
        
        trimmedline = switchline.replace(' ', '').replace('\t', '').replace('\n', '')
        commentline = is_comment_line(trimmedline)
        
        groupline = trimmedline.startswith('[')
            
        # Start of comment block.
        if trimmedline.startswith("/*"):
            incommentblock = True
        # Group
        elif groupline:
            groupname = get_groupname_from_line(trimmedline)
            
        # Start of switch data (not a comment/group declaration, has data separators...)
        if ((not incommentblock) and (not commentline) and (not groupline) and
            (SWITCH_SEPARATOR in switchline)):
            # Actual switch data.
            newswitch = parse_switchdata(switchline)
            newswitch.group = groupname    
            # Build switch.
            if newswitch is None:
                print "skipping switch: " + switchline
            else:
                good_switches.append(newswitch)
        
        # End of comment block
        if trimmedline.endswith("*/"):
            incommentblock = False
            
    # finished.
    return good_switches

def is_comment_line(line_):
    """ determines if a single line is a comment for switches config,
        allows the same logic to be used whereever switch parsing is done.
        unfortunately, this doesn't cover block comments with /* and */.
    """
    line_ = line_.replace(' ', '').replace('\t', '').replace('\n', '')
    return (line_.startswith('#') or line_.startswith('//') or line_.startswith(';'))

def parse_switchdata(switchline):
    """ retrieves individual items from switchdata text line.
        this works on a single line only, parsing whole files is done with read_file().
        ex:
            myswitch = parse_switchdata("setting.py|name|on_val,off_val|FINDER_TEXT|description")
        returns None on failure.            
    """
    switchline = strip_chars(switchline, (' ', '\t', '\n', '|'))
    # may contain an empty value, this would break everything.
    if '||' in switchline: return None
    
    switchdata = switchline.split('|')
    data_len = len(switchdata)
    skip = False
    if (data_len < SWITCH_LEN - 1) or (data_len > SWITCH_LEN):
        print "\nbad switch data, wrong item length: " + switchline
        sw_file = name = values = finder = desc = None
        skip = True
    else:
        # parse switch data
        sw_file = switchdata[0].strip(' ').strip('\t')
        if sw_file.startswith('|'): sw_file = sw_file[1:]
        # name
        name = switchdata[1]
        # has aliases?
        if ',' in name:
            name = [n.strip(' ') for n in name.split(',')]
        # possible values.
        values = parse_values(switchdata[2])
        # error parsing values?
        if isinstance(values, (str, unicode)):
            print values + switchline
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
            if desc.endswith(SWITCH_SEPARATOR) or desc.endswith('\n'): desc = desc[:-1]
            if len(desc) == 0: desc = None
        newswitch = None if skip else switch(sw_file, name, values, finder, desc)
        return newswitch


def get_groupname_from_line(line_):
    """ parses a groupname out of a single line in switches.conf,
        returned None on failure, or end of group "[/mygroup]".
        allows the same logic to be used everywhere switches are parsed from file.
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

        
def parse_values(values):
    """ retrieve a list of two values from a values string (value1, value2).
        handles lists/tuples/quotes/etc.
        returns values list of 2 items on success.
        returns error string on failure.
    """
    if ',' in values:
        # reg ex for finding proper value separator.
        # some times a comma is needed for proper values (lists, tuples, dicts, quoted strings)
        sep_pattern = re.compile('["\'\\}\\]\\)][ ]{0,50},[ ]{0,50}["\'\\{\\[\\(]')
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
                # quoted items within list/tuple values. find the actual separator
                value_sep = find_unique_item(sep_find)
                #print_debug("UNIQUE ITEM: " + value_sep)
            # chars to fill in missing pieces because of regex separator search result
            val2_start = value_sep.replace(' ', '')[-1]
            val1_end = value_sep.replace(' ', '')[0]
    
        values = [v.strip(' ') for v in values.split(value_sep)]
        #print_debug("Sep: " + value_sep + '\nValues: ' + ' | '.join(values) + '\nStart/End: ' + val2_start + val1_end)
        
        if len(values) <> 2:
            values = "\nbad switch data, too many possible values: "
        else:
            # fix missing start/end from regex.
            values[0] = values[0] + val1_end
            values[1] = val2_start + values[1]
                
    else:
        values = "\nbad switch data, not enough possible values: "
    
    return values


def validate_switches():
    """ make sure switches aren't duplicates, and groups don't have the same name as switches. """
    
    if switches is None:
        print_fail("no switches to validate!\nrun 'wpswitch help' for more info...")
    
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
            if not switch_name in duplicate_switches:
                duplicate_switches.append(switch_name)
        if switch_name in group_names:
            if not switch_name in switch_group_conflicts:
                switch_group_conflicts.append(switch_name)
    
    err_count = len(duplicate_switches + switch_group_conflicts)
    if err_count > 0:
        if len(duplicate_switches) > 0:
            print "duplicate switch names found!:"
            for dupe_switch in duplicate_switches:
                print '    ' + dupe_switch
        if len(switch_group_conflicts) > 0:
            print "conflicting switch and group names found!:"
            for conflict in switch_group_conflicts:
                print '    ' + conflict
        print '\nswitch config errors found: ' + str(err_count)  + \
              '\nplease correct these errors and try again...'
        sys.exit(1)
        
def write_file(filename = 'switches.conf', dryrun = False):
    """ Writes all switches to file.
        Warning: This will overwrite the existing switches.conf.
                 All comments will be replaced, and switches will be 
                 re-ordered (groups will be correct).
    """
    
    filepath = file_exists(filename)
    if not filepath:
        print_fail("switches file not found!: " + filename)
    newcontents = []
    for groupname in get_groups():
        newcontents.append('[' + groupname + ']\n')
        groupswitches = get_group_members(groupname)
        newcontents.append('    ' + '\n    '.join([sw.get_switch_str() for sw in groupswitches]))
        newcontents.append('\n[\\' + groupname + ']\n')
    
    if dryrun:
        print "\nwriting file: " + filename + '\n\n'
        print ''.join(newcontents)
        return True
    else:
        try:
            with open(filename, 'w') as fwrite:
                fwrite.writelines(newcontents)
                return True
        except (OSError, IOError) as exio:
            print_fail("unable to write switches file: " + filename + '\n' + str(exio))
        except Exception as ex:
            print_fail("error writing switches file: " + filename + '\n' + str(ex))
    return False
        
def write_switch_line(switch_, prev_switch=None, filename='switches.conf', dryrun = False):
    """ Replace an old switch line with a new one in switches.conf,
        If prev_switch is not passed, the new switch is simply added to the end.
        * switch_ must be a valid switch().
    """
    #@todo: Add Group Handling! (groups would be nice.)
    
    filepath = file_exists(filename)
    if not filepath:
        print_fail("switches file does not exist!: " + filename)
    
    try:
        oldlines = []
        with open(filepath) as fread:
            oldlines = fread.readlines()
    except (OSError, IOError) as exio:
        print_fail("unable to read file for editing: " + filename + '\n' + str(exio))
    except Exception as ex:
        print_fail("error reading file for edit: " + filename + '\n' + str(ex))
    
    switchstr = switch_.get_switch_str()
    
    editedlines = []
    commentblock = False
    replaced = False
    for oldline in oldlines:
        # line will not be changed unless it needs to be replaced by the new one.
        editedline = oldline
        oldtrim = strip_chars(oldline, (' ', '\t', '\n'))
        
        # start of comment block?
        if oldtrim.startswith('/*'): commentblock = True
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
            # get current line's switch()
            oldswitch = parse_switchdata(oldline)
            
            # is this the switch to be replaced?
            if (oldswitch is not None) and (oldswitch.get_name() == switch_.get_name()):
                # replacing previous switch? check the group name
                if ((prev_switch is not None) and 
                    (oldswitch.get_name() == prev_switch.get_name())):
                    # warn about changing groups (for now)
                    if prev_switch.group != switch_.group:
                        oldgroup = str(prev_switch.group)
                        newgroup = str(switch_.group)
                        print '\n'
                        print_block(("** warning: ", 
                                     "group has changed from '" + oldgroup + "' to '" + newgroup + "'.",
                                     "this switch is being placed in '" + str(groupname) + "'."))
                              
                # Replace old switch setting.
                editedline = oldline.replace(oldtrim, switchstr)
                if dryrun: 
                    print '\n'
                    print_block((("replacing old switch: ", oldtrim), 
                                 ('with: ', switchstr)))
                    
                replaced = True

        # add the line (edited or not)
        editedlines.append(editedline)
        # end of comment block?
        if oldtrim.endswith('*/'): commentblock = False
    
    # Add as new switch
    if not replaced:
        if dryrun: print "\nadding new line:\n    " + switchstr
        editedlines.append(switchstr)
    
    # Write new file
    if dryrun:
        print "\n\nwriting file " + filename + "..."
        print ''.join(editedlines)
    else:
        try:
            with open(filepath, 'w') as fwrite:
                fwrite.writelines(editedlines)
        except (OSError, IOError) as exio:
            print_fail("unable to write file for editing: " + filename + '\n' + str(exio))
        except Exception as ex:
            print_fail("error writing file for edit: " + filename + '\n' + str(ex))
    
    return True
        
        
     
def validate_args(args):
    """ makes sure valid arguments are passed. """
    
    name = args[0]
    is_command = (name.lower() in good_commands)
    
    if len(args) < 2:
        if not is_command:
            print_usage("Missing argument!")
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
            print_fail("switch/command not found: " + name)
        # check possible values
        if not val.lower() in good_switch_args:
            print_usage("Bad switch value!: " + val + '\n' + \
                       "Expecting: " + ', '.join(good_switch_args))
            sys.exit(1)
    
    # return arguments as: (name, value, (all other args, or empty list))
    return [name, val, other_args]


def find_unique_item(items):
    """ finds the unique list/tuple item """
    
    trimmed_list = [i.replace(' ', '') for i in items]
    for i in range(0, len(trimmed_list)):
        item = trimmed_list[i]
        if trimmed_list.count(item) == 1:
            # return original item, not trimmed.
            return items[i]

def cmdline_build_switch(initial_name=None, dryrun = False, filename = 'switches.conf'):
    """ interactive 'switch builder/editor' in the console, 
        parses input to build a switch, validates info, and adds it to switches.conf.
    """

    sw = get_switch_byname(initial_name)
    if sw is None:
        oldswitch = None
        sw = switch()
        header = "Ready to build switch: "
        if initial_name is not None: header += initial_name
        print header + '\n'
    else:
        # save old switch for comparison during switch-write.
        oldswitch = copy.deepcopy(sw)
        print "Editing switch: " + sw.name + '\n'
    
    # prints prompts with current values (if any value is present)
    def prompt_val(s, val):
        max_prompt_len=60
        if s.endswith(':'): s = s[0:-1]
        if val is None:
            s = s + ':'
        else:
            s = s + ' [' + str(val) + ']:'
        return (' ' * (max_prompt_len - len(s))) + s + ' '
    
    # Build list of current switch names to check against (aliases included)
    switch_names = [eachswitch.name for eachswitch in switches]
    #switch_aliases = []
    for aliaslst in [eachswitch.aliases if (eachswitch.aliases is not None) else [] for eachswitch in switches]:
        switch_names += aliaslst
    
    
    # remove this name from the list if a name is set,
    # we will be using the list of names to block answers to the "name:" prompt.
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

        name = cmdline_get_response(prompt_val("Name", names), 
                                    default_value=names,
                                    blocked_values=switch_names)
        if ',' in name:
            # Set new aliases
            aliases += [a.strip(' ') for a in name.split(',')]
            name = aliases[0]
        else:
            if sw.aliases is not None:
                remove_aliases = cmdline_get_response(prompt_val("Remove Aliases? (y/n)", "n"),
                                                      acceptable_values = ("y", "n", "yes", "no"),
                                                      default_value = "n",
                                                      allow_blank = False)
                if remove_aliases.startswith('y'):
                    aliases = []
        
        # remove duplicates from aliases.
        for aliasdupe in [a for a in aliases]:
            if aliases.count(aliasdupe) > 1: aliases.remove(aliasdupe)
        sw.name = name
        sw.aliases = None if aliases == [] else aliases

        # Group?
        group = cmdline_get_response(prompt_val("Group", str(sw.group)), 
                                     default_value = str(sw.group),
                                     allow_blank=True)
        if group == '':
            group = None
        sw.group = group
        
        # Get filename
        sw.filename = cmdline_get_response(prompt_val("Target File", sw.filename), 
                                           default_value=sw.filename,
                                           file_must_exist=True)
        
        # Get finder
        sw.finder = cmdline_get_response(prompt_val("Target String (Finder)", sw.finder),
                                         default_value=sw.finder)
    
        
        # Get Values
        if sw.values is None:
            onvalue = None
            offvalue = None
        else:
            onvalue = sw.values[0]
            offvalue = sw.values[1]
            
        onvalue = cmdline_get_response(prompt_val("On Value", onvalue),
                                       default_value=onvalue)
        offvalue = cmdline_get_response(prompt_val("Off Value", offvalue),
                                        default_value=offvalue)
        sw.values = (onvalue, offvalue)
    
        # Get Description
        sw.description = cmdline_get_response(prompt_val("Description", sw.description), 
                                       default_value=sw.description,
                                       allow_blank=True)
        
        # Set values
        if sw == oldswitch:
            if dryrun:
                print "\nswitches are still equal,\nwould've wrote: " + sw.get_switch_str()
            else:
                print "\nswitch not changed."
        else:
            print "\nwriting switch: " + sw.get_name()
            #if write_file(filename, dryrun):
            if write_switch_line(sw, oldswitch, filename, dryrun):
                print "...success."
        
    except cmdlineExit as excancel: #@UnusedVariable: excancel
        print "\nswitch editing cancelled, no changes were made.\n"
    
        

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
        blocked_values    : same as acceptable but reverse, we won't allow them.
        file_must_exist   : response must be an existing file name/path (full or relative)
                            [default: False]
        condition         : condition to check before allowing this answer
                            [default: True]
    """
    allow_blank = get_dict_val(kwargs, 'allow_blank', False)
    default_value = get_dict_val(kwargs, 'default_value', None)
    max_length = get_dict_val(kwargs, 'max_length', 255)
    acceptable_values = get_dict_val(kwargs, 'acceptable_values', None)
    blocked_values = get_dict_val(kwargs, 'blocked_values', None)
    file_must_exist = get_dict_val(kwargs, 'file_must_exist', False)
    condition = get_dict_val(kwargs, 'condition', True)
    
    def answer_warn(s):
        print '\n' + s
        print '...type !exit, !cancel, or !quit to cancel building this switch.\n'
        
    # this traps the EOFError that is raised on user cancelling...
    # a cmdlineExit() is raised instead, same as when '!exit' is the response.
    # the calling function should trap cmdlineExit()... (cmdline_build_switch())
    try:
        while True:
            response = raw_input(prompt)
            response_trim = response.replace(' ', '').lower()
            response_multicheck = response_trim.replace(',', '')
            
            # first checks (exit, blank, max_len, acceptable answer)
            if (response_trim in ('!exit', '!cancel', '!quit')):
                raise cmdlineExit("User Cancelled")
            # Blank, use default value
            elif (response_trim == '' and (default_value is not None)):

                return default_value
            # Blank, no default, no blanks allowed
            elif (response_trim == '' and (not allow_blank)):
                answer_warn("You must provide an answer.")
            # All commas, weird, but would mess up the Name/Aliases prompt.
            elif (response_multicheck == '' and (not allow_blank)):
                answer_warn("Commas are for entering multiple values where accepted, but values cannot be empty.")
            # Max Length
            elif (len(response) > max_length):
                answer_warn("Answer was too long! > " + str(max_length)) + " characters."
            # Acceptable Values
            elif ((acceptable_values is not None) and (response_trim not in acceptable_values)):
                answer_warn("Not an acceptable value. Has to be one of:\n    " + '\n    '.join(acceptable_values))
            # Blocked Values
            elif ((blocked_values is not None) and (response_trim in blocked_values)):
                answer_warn("Not an acceptable value. Cannot be one of:\n    " + '\n    '.join(blocked_values))
            # Must be a file that exists
            elif (file_must_exist and (not os.path.isfile(response))):
                answer_warn("File must exist (relative, or full path).")
            
            # All other checks passed
            else:
                # final check (condition)
                if condition:
                    return response
            
    except EOFError as exeof: #@UnusedVariable: exeof
        raise cmdlineExit("User Cancelled")
    except KeyboardInterrupt as exkey: #@UnusedVariable: exkey
        raise cmdlineExit("User Cancelled")
    

def get_dict_val(dict_, key, default_val=None):
    """ safely retrieves dict values,
        returns None on failure/missing key
    """
    
    if dict_.has_key(key):
        return dict_[key]
    return default_val


def strip_chars(str_, char_list=None):
    """ strips all characters in the list using strip() """
    
    if char_list is None: char_list = (' ', '\t', '\n')
    
    for ch in char_list:
        str_ = str_.strip(ch)
    return str_
    
def print_debug(s):
    """ just a wrapper for print that can be easily searched for and replaced. """
    
    print s

def print_help():
    """ print a long message about how to configure and use wpswitch """
    
    print help_str
    
def print_usage(sreason=None):
    """ prints usage, with a reason for showing it if needed """
    
    if sreason is not None:
        print sreason
    
    print usage_str

def print_fail(sreason=None):
    """ exits the script, with a reason given if needed. """
    
    if sreason is not None:
        print sreason
    print '\nGoodbye.\n'
    sys.exit(1)

def print_block(msgdata, max_line_len=80):
    """ prints formatted blocks of text like:
        print_block(("warning: ", "line1", 
                                  "line 2"))
        print_block(("warning: ", "line2\nline2")
        print_block((("warning2: ", "test"), 
                     ("sub-warning:", "test2")))
    """
    def get_longest_tag(taglist):
        current_len = 0
        for tagname in taglist:
            if isinstance(tagname, (list, tuple)): tagname = tagname[0]
            if len(tagname) > current_len: current_len = len(tagname)
        return current_len
    taglen = get_longest_tag(msgdata)
    def format_tag(tagname, len_):
        return (' ' * (len_ - len(tagname))) + tagname
    def format_val(val, len_):
        return (' ' * len_) + val
    def parse_vals(valraw):
        outvals = []
        for val in valraw:
            if '\n' in val:
                outvals += val.split('\n')
            else:
                outvals.append(val)
        return outvals

    fixedvals = []
    # simple 1 tag with values tuple
    if isinstance(msgdata[0], (str, unicode)):
        tagname = msgdata[0]
        taglen = len(tagname)
        rawvalues = msgdata[1:]
        fixedvals = parse_vals(rawvalues)
        print tagname + fixedvals[0]
        for val in fixedvals[1:]:
            print format_val(val, taglen)
    # multiple tags, each item is a tuple with (tagname, value1, value2..)
    elif isinstance(msgdata[0], (list, tuple)):
        taglen = get_longest_tag(msgdata)
        for mainitem in msgdata:
            tagname = mainitem[0]
            rawvalues = mainitem[1:]
            fixedvals = parse_vals(rawvalues)
            print format_tag(tagname, taglen) + fixedvals[0]
            for val in fixedvals[1:]:
                print format_val(val, taglen)
                
# START OF SCRIPT -------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage("No arguments given!")
        sys.exit(1)
        
    main(sys.argv[1:])
