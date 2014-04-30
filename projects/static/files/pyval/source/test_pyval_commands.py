#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from pyval_commands import AdminHandler, CommandHandler


# Only load admin help once, and save it here.
ADMINHELP = None


class NoCommand(object):

    """ Helper for get_usercmd_result, where returning None could mean
        several different things. Instead of returning None when no
        handler function is found, return NoCommand('your message')
        so the caller can recognize the difference.
    """

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return str(self.msg)

    def __repr__(self):
        return str(self.msg)


class TestCommandFuncs(unittest.TestCase):

    """ Test basic functionality of pyval_commands.
        This includes AdminHandler, CommandHandler, and CommandFuncs.
    """

    def fail_nocmd(self, nocmd):
        """ Fail due to NoCommand. Pass a NoCommand in. """

        self.fail('No cmd handler for: {}'.format(nocmd))

    def get_cmdfunc(self, cmdhandler, userinput, asadmin=False):
        """ Receives input like it came from chat, returns handler func. """
        if not cmdhandler:
            self.fail('No cmdhandler set in get_cmdfunc!')

        cmd, sep, args = userinput.partition(' ')
        usernick = 'testadmin' if asadmin else 'testuser'
        cmdfunc = cmdhandler.parse_data(usernick, '#channel', userinput)
        if cmdfunc:
            return cmdfunc
        else:
            return NoCommand(userinput)

    def get_usercmd_result(self, cmdhandler, userinput, asadmin=False):
        """ Receives input like it came from chat, returns cmd output. """
        if not cmdhandler:
            self.fail('No cmdhandler set in get_usercmd_result!')

        cmdfunc = self.get_cmdfunc(cmdhandler, userinput, asadmin=asadmin)
        if cmdfunc:
            cmd, sep, args = userinput.partition(' ')
            usernick = 'testadmin' if asadmin else 'testuser'

            return cmdfunc(args, nick=usernick)
        else:
            return NoCommand(userinput)

    def is_nocommand(self, o):
        """ Test whether an object is actually a NoCommand(). """
        return isinstance(o, NoCommand)

    def setUp(self):
        """ Setup each test with an admin/command handler """
        global ADMINHELP
        if ADMINHELP:
            self.adminhandler = AdminHandler(help_info=ADMINHELP)
        else:
            self.adminhandler = AdminHandler()
            ADMINHELP = self.adminhandler.help_info
        self.adminhandler.nickname = 'testnick'
        self.adminhandler.admins.append('testadmin')
        self.cmdhandler = CommandHandler(adminhandler=self.adminhandler)

    def test_admin_getattr(self):
        """ admin command !getattr works """

        self.cmdhandler.admin.blacklist = True

        cmdresult = self.get_usercmd_result(self.cmdhandler,
                                            '!getattr admin.blacklist',
                                            asadmin=True)
        if self.is_nocommand(cmdresult):
            self.fail_nocmd(cmdresult)

        self.assertEqual(cmdresult, 'admin.blacklist = True',
                         msg='Failed to get attribute')

    def test_admin_setattr(self):
        """ admin command !setattr works """

        self.cmdhandler.admin.blacklist = False
        cmd = '!setattr'
        args = 'admin.blacklist True'
        userinput = '{} {}'.format(cmd, args)
        setattrfunc = self.get_cmdfunc(self.cmdhandler,
                                       userinput,
                                       asadmin=True)
        if self.is_nocommand(setattrfunc):
            self.fail_nocmd(setattrfunc)

        self.assertEqual(self.cmdhandler.admin.blacklist, False,
                         msg='Failed to setup attribute correctly')
        setattrfunc(args, nick='testadmin')
        self.assertEqual(self.cmdhandler.admin.blacklist, True,
                         msg='Failed to set attribute')

    def test_print_topastebin(self):
        """ test print_topastebin() """

        pastebin = self.cmdhandler.commands.print_topastebin

        noneresult = pastebin('', '')
        self.assertIsNone(noneresult, msg='empty arg should produce None')

        pastebinurl = pastebin('<pyvaltest> query', '<pyvaltest> valid string')
        self.assertIsNotNone(pastebinurl,
                             msg=('print_topastebin() failed to give url: '
                                  '\'{}\''.format(pastebinurl)))
        # Make sure it is an actual url.
        self.assertIsNotNone(pastebinurl,
                             msg='valid string should produce a paste bin url')
        print('test_print_topastebin - Url: {}'.format(pastebinurl))

if __name__ == '__main__':
    unittest.main()
