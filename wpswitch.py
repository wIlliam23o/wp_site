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

#@attention: NOT COMPLETELY WORKING, has no 'setters'
#@todo: COMPLETE 'set functions'

import sys
import os.path
import re # for regex 'finders'

usage_str = """
    usage: wpswitch <command>|<switch_name on|off|-|?|!|@> [options]
    
    commands:
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
         description: just a short comment/description about this switch, or empty like: {}
         
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
        
        file = str(self.filename)
        
        if self.aliases is None:
            names = str(self.name)
        else:
            names = str(','.join(self.aliases))
        
        if self.values is None:
            values = 'None'
        else:
            values = str(','.join(self.values))
        
        finder = str(self.finder)
        desc = str(self.description)
        
        return str(SWITCH_SEPARATOR.join([file, names, values, finder, desc]))
            
        
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
good_commands = ("help", "names", "status", "values", "full", "groups")

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
        do_command(name.lower(), val)
 
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
    
    #@todo: toggle state.
    #@todo: Do actual 'switching.' (it's late tonight)

def do_command(name, val):
    """ perform a simple command and exit. """
    
    if val is not None:
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
            

def get_groups():
    """ returns a list of group names """
    groups = []
    for sw in switches:
        if sw.group is not None:
            if not sw.group in groups: groups.append(sw.group)
    return groups
    

def get_group_members(groupname):
    """ get all switches in a group.
        returns list of members.
    """
    
    if groupname == '-' or groupname == '':
        groupname = 'None'
        
    members = []
    for sw in switches:
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
        
def get_switch_byname(name):
    """ retrieves switch by name """
    
    for sw in switches:
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
        (what the switch should toggle to)
    """
    
    if not isinstance(name_or_switch, (switch)):
        name_or_switch = get_switch_byname(name_or_switch)
    oldval = name_or_switch.get_state()
    return "off" if oldval == "on" else "on"


def read_file(filename="switches.conf"):
    """ reads a set of switches from a file. """
    
    if not os.path.isfile(filename):
        filename = os.path.join(sys.path[0], filename)
        if not os.path.isfile(filename):
            print_fail("switches file does not exist!: " + filename)
    
    try:
        with open(filename) as fread:
            lines = fread.readlines()
    except Exception as ex:
        print_fail("unable to read file: " + filename + '\n' + \
                   str(ex))
    
    good_switches = []
    incommentblock = False
    groupline = False
    groupname = None
    
    for switchline in lines:
        trimmedline = switchline.replace(' ', '').replace('\t', '').replace('\n', '')
        commentline = trimmedline.startswith("#") or trimmedline.startswith("//")
        groupline = trimmedline.startswith('[')
        
        # Start of comment block.
        if trimmedline.startswith("/*"):
                        incommentblock = True
        # Group
        elif groupline:
            # end of group.?
            if trimmedline.startswith('[/'):
                groupname = None
            else:
                # start, get group name
                groupname = trimmedline[1:-1]
            
        # Start of switch data (not a comment/group declaration, has data separators...)
        if ((not incommentblock) and (not commentline) and (not groupline) and
            (SWITCH_SEPARATOR in switchline)):
            # Actual switch data.
            switchdata = switchline.split(SWITCH_SEPARATOR)
            sw_file, name, values, finder, desc, skip = parse_switchdata(switchdata)
                 
            # Build switch.
            if skip:
                if name is None:
                    name = "'unknown switch name'"
                else:
                    name = "'" + name + "'"
                print "skipping " + name + "..."
            else:
                good_switches.append(switch(sw_file, name, values, finder, desc, groupname))
        
        # End of comment block
        if trimmedline.endswith("*/"):
            incommentblock = False
            
    # finished.
    return good_switches


def parse_switchdata(switchdata):
    """ retrieves individual items from switchdata text line. """
    data_len = len(switchdata)
    skip = False
    if (data_len < SWITCH_LEN - 1) or (data_len > SWITCH_LEN):
        print "bad switch data, wrong item length: " + switchdata.strip(' ').strip('\t').strip('\n')
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
            print values + switchdata.strip(' ').strip('\t').strip('\n')
            skip = True
            
        # finder text
        finder = switchdata[3]
        if finder.endswith(SWITCH_SEPARATOR) or finder.endswith('\n'):
            finder = finder[:-1]
            desc = None
        
        # possible description
        if len(switchdata) > 4:
            desc = switchdata[4]
            if desc.endswith(SWITCH_SEPARATOR) or desc.endswith('\n'): desc = desc[:-1]
            if len(desc) == 0: desc = None
        
        return sw_file, name, values, finder, desc, skip
    
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
            values = "bad switch data, too many possible values: "
        else:
            # fix missing start/end from regex.
            values[0] = values[0] + val1_end
            values[1] = val2_start + values[1]
                
    else:
        values = "bad switch data, not enough possible values: "
    
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

    
# START OF SCRIPT -------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage("No arguments given!")
        sys.exit(1)
    main(sys.argv[1:])
