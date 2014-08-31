'''
    aliasmgr_cmdline.py
    Command-line interface for Alias Manager.
Created on Sep 24, 2013

@author: Christopher Welborn
'''
import sys
import os
import re

import aliasmgr_util as amutil
# settings helper
settings = amutil.settings


class CmdLine():

    """ alias manager command line tools """

    def __init__(self, largs=None):
        """ Loads command-line interface, must pass args (largs). """
        # aliasfile can be replaced by arg_handler().
        self.aliasfile = settings.get('aliasfile')
        # load all aliases/functions (list of amutil.Command() objects)
        self.commands = amutil.readfile()

    def main(self, largs):
        """ runs command line style, accepts args """
        # Arg
        if len(largs) > 0:
            ret = self.arg_handler(largs)
            return ret
        else:
            print('No arguments supplied to aliasmgr.CmdLine!')
            return 1

    def arg_handler(self, largs):
        """ receives list of args, handles accordingly """

        # scan for alias file to use.
        for sarg in largs:
            if (os.path.isfile(sarg) or
                os.path.isfile(os.path.join(sys.path[0], sarg))):
                self.aliasfile = sarg
                self.commands = amutil.readfile(aliasfile=self.aliasfile)
                largs.remove(sarg)

        # notify user about which alias file is being used.
        print('\nUsing alias file: {}\n'.format(self.aliasfile))
        # get lower() list of alias names
        if self.commands:
            aliasnames = [cmd.name.lower() for cmd in self.commands]
        else:
            aliasnames = []

        # scan for normal args.
        for sarg in largs:
            if sarg.lower() in aliasnames:
                self.printalias(sarg)
            elif sarg.startswith(('-h', '--help')):
                # HELP
                self.printusage()
                self.printhelp()
                return 0
            elif sarg.startswith(('-v', '--version')):
                # VERSION
                self.printver()
                return 0
            elif sarg.startswith(('-e', '--export')):
                # EXPORTS
                return self.printexports()
            elif sarg.startswith(('-p', '--p')):
                # PRINT aliases (sarg will tell us normal/short/comment/or full style)
                return self.printaliases(sarg)
            elif sarg.startswith(('-C', '--convert')):
                # CONVERT command to its own script file.
                return self.convert_toscript(largs)
            else:
                # Search automatically ran
                return self.printsearch(sarg)

    def convert_toscript(self, cmdlineargs):
        """ Convert an alias/function to a script file. """
        args = cmdlineargs[:]
        overwrite = False
        for i, arg in enumerate(args[:]):
            if arg.startswith('-'):
                args.pop(i)
                if arg.lower() in ('-o', '--overwrite'):
                    overwrite = True

        arglen = len(args)
        if (arglen not in [1, 2]):
            print('\nExpecting: AliasName [TargetFile] [--overwrite]')
            return 1
        if len(args) == 2:
            aliasname, targetfile = args
        else:
            aliasname = args[0]
            targetfile = None

        matches = self.searchalias(aliasname)
        if len(matches) > 1:
            print('\nAmbiguos name, returned many results:')
            print('    {}'.format('\n    '.join(c.name for c in matches)))
            return 1

        cmd = matches[0]
        newfile = cmd.to_scriptfile(filepath=targetfile, overwrite=overwrite)
        if newfile:
            print('Script was generated: {}'.format(newfile))
            return 0
        print('\nUnable to generate script: {}'.format(newfile))
        return 1

    def printver(self):
        print('{}\n'.format(settings.versionstr))

    def printusage(self):
        usagelines = (
            settings.versionstr,
            '         Usage:',
            '            aliasmgr',
            '                     ...run the alias manager gui.',
            '            aliasmgr <alias_name>',
            '                     ...list info about an existing alias/function.',
            '            aliasmgr -C <alias_name> [<target_file>] [-o]',
            '                     ...convert an alias/function into a stand-alone script.',
            '            aliasmgr [file] -p | -h | -v | -e',
            '                     ...list info about all aliases/functions. Use specific alias file if given.',
        )
        print('{}\n'.format('\n'.join(usagelines)))

    def printhelp(self):
        aliasfile = settings.get("aliasfile")
        if aliasfile == "":
            aliasfile = "(Not selected yet)"
        helplines = (
            "  Current file:    {}\n".format(aliasfile),
            "      Commands:",
            "                  -h : Show this help message",
            "                  -v : Print version",
            "                  -e : Print exported names only",
            "                  -C : Convert a function/alias to its own script file.",
            "                  -o : Overwrite existing files when converting to scripts.",
            "     -p[s|c][f|a]    : Print current aliases/functions.",
            "                -pxf : Print entire functions (with content).",
            '    Formatting:',
            "                   x : will print entire functions, does nothing for aliases.",
            "                   s : only shows names",
            "                   c : shows names : comments\n",
            "         Types:",
            "                   a : shows aliases only",
            "                   f : shows functions only\n",
            "       Example:",
            '           \'aliasmgr myshortcut\' will show any info found for alias/function called \'myshortcut\'',
            '           \'aliasmgr -pcf\' shows names and comments for functions only',
            '           \'aliasmgr -psa\' shows just the names for aliases (not functions).'
        )
        print('{}\n'.format('\n'.join(helplines)))

    def printalias(self, aliasname):
        """ Print a single alias (retrieved by name or Command() object) """

        if isinstance(aliasname, amutil.Command):
            self.printcommand(aliasname)
        else:
            # retrieve by name.
            aliasnames = [cmd.name for cmd in self.commands]
            if aliasname in aliasnames:
                self.printcommand(self.commands[aliasnames.index(aliasname)])
            else:
                print('\nNo alias by that name!: {}'.format(aliasname))
                return 1
        return 0

    def printcommand(self, cmdobj, showcommand=True):
        """ Print a Command() object, with some formatting. """

        sexported = 'Yes' if cmdobj.exported.lower() == 'new' else cmdobj.exported

        sformatted = '    Name: {}\n'.format(cmdobj.name) + \
                     ' Comment: {}\n'.format(cmdobj.comment) + \
                     'Exported: {}'.format(sexported)
        # include command?
        if showcommand:
            sformatted += '\n Command:\n  {}\n'.format('\n  '.join(cmdobj.cmd))

        print('{}'.format(sformatted))

    def printsearch(self, aliasname):
        """ Searches aliases for aliasname (regex), and prints results """

        matches = self.searchalias(aliasname)
        if matches:
            usedivider = (len(matches) > 1)
            lastmatch = matches[-1]
            for cmdinfo in matches:
                self.printcommand(cmdinfo, showcommand=False)
                if usedivider and (cmdinfo != lastmatch):
                    print('-' * 40)
            print('\nFound {} matches for: {}\n'.format(str(len(matches)), aliasname))
            return 0
        else:
            print('\nNo aliases found matching: {}\n'.format(aliasname))
            return 1

    def searchalias(self, aliasname):
        """ Searches and retrieves all aliases matching aliasname (regex) """

        try:
            repat = re.compile(aliasname, flags=re.IGNORECASE)
        except:
            print('\nInvalid alias name given!: {}\n'.format(aliasname))
            return []

        matches = []
        for cmdinfo in self.commands:
            wholecmd = '{} {} {} {}'.format(cmdinfo.name,
                                            cmdinfo.cmd,
                                            cmdinfo.comment,
                                            cmdinfo.exported)
            matchcmd = repat.search(wholecmd)
            if matchcmd:
                matches.append(cmdinfo)

        return matches

    def printaliases(self, sarg):
        """ Print aliases in current file """

        if self.commands:
            for itm in self.commands:
                # Comments?
                if len(itm.comment) > 0:
                    # Add Comment
                    scomment = itm.comment
                else:
                    scomment = "(No Comment)"
                # Exported?
                sexport = itm.exported
                # Print Name
                if "s" in sarg:
                    # printing short version, names only
                    sfinalname = (itm.name)
                elif "c" in sarg:
                    # print comment version, names/comments only
                    maxcmdlength = 20
                    thiscmdlength = len(itm.name)

                    sfinalname = (itm.name +
                                 (" " * (maxcmdlength - thiscmdlength)) +
                                  ": " + scomment)
                else:
                    # printing normal (p), or full version (px)
                    sfinalname = (itm.name + ":")
                    # Show comment/export/command
                    sfinalname += ("\n    Comment: " + scomment + "\n     Export: " + sexport)
                    # Function, show full cmd list?
                    if itm.isfunction():
                        # Function, show all commands?
                        if "x" in sarg:
                            # Build full command items string
                            scmd = "    Command:\n"
                            for itmcmd in itm.cmd:
                                scmd += "             " + itmcmd + '\n'
                        else:
                            # Only show first line of function
                            scmd = "    Command:\n" + \
                                   "             " + itm.cmd[0] + " (more lines...)\n"
                    else:
                        # Simple 1 liner, alias
                        scmd = "    Command:\n             " + itm.cmd[0] + '\n'

                    sfinalname += '\n' + scmd

                # Final output built, print all/aliases/functions
                if "a" in sarg:
                    # Aliases only (also empty commands)
                    if not itm.isfunction():
                        print(sfinalname)
                elif "f" in sarg:
                    # Functions only
                    if itm.isfunction():
                        print(sfinalname)
                else:
                    # All
                    print(sfinalname)
        else:
            # No items found
            print('\nNo items found in alias file: {}'.format(self.aliasfile))
            return 1
        return 0

    def printexports(self):
        """ Prints exports only """
        exports = [f.name for f in self.commands if f.exported.lower() == 'yes']
        if exports:
            print('\n'.join(exports))
            return 0
        else:
            print('\nNo exports found!\n')
            return 1
