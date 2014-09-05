#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Welborn Productions - Switches - Tests
        Tests wpswitch.py for regression, accuracy, and more.

    -Christopher Welborn May 18, 2013
'''

# Meant to be ran with './manage.py test scripts' (django test runner)
import sys
import os
import os.path
import unittest
import unittest.main
from scripts import wpswitch
# Make the wpswitch module quiet.
wpswitch.printerror = lambda s: None

# Test data to be used (should be valid, well-formed switch data).
test_data_local = """
test_switches_target.txt|testnogroupswitch|True,False|testnogroupswitch =|a switch with no group...

[testgroup]
    # A test comment.
    ; another test comment.
    // a c/js style comment.
    /* a comment
        block. */
    test_switches_target.txt|testswitch, testswitchalias|True,False|testswitch =|a test switch...
    test_switches_target.txt|testswitch2, switch2|1,0|testswitch2 =|another test switch...
[/testgroup]

[testgroup2]
    test_switches_target.txt|testswitchregex|str(26),str(27)|/test\w+regex =/|testing regex finders...
[/testgroup2]

"""
# Line from test_data_local (just here so split() doesn't have to be used more than once on test data)
test_lines_local = test_data_local.split('\n')


# Expected group names (from test_data_local, include 'None')
GROUP_MEMBERS = {'None': ['testnogroupswitch'],
                 'testgroup': ['testswitch', 'testswitch2'],
                 'testgroup2': ['testswitchregex'],
                 }
# Test target file.
TEST_TARGET_FILE = "test_switches_target.txt"
if os.path.isfile(TEST_TARGET_FILE):
    USE_TEST_TARGET_FILE = True
else:
    TEST_TARGET_FILE = os.path.join(sys.path[0], TEST_TARGET_FILE)
    USE_TEST_TARGET_FILE = os.path.isfile(TEST_TARGET_FILE)

# Temporary switches.conf to create.
TEST_CONF = os.path.join(sys.path[0], 'test_switches.conf')
try:
    with open(TEST_CONF, 'w') as ftestconf:
        ftestconf.write("okay")
        USE_TEST_CONF = True
except Exception as exio:
    print("Cannot create temporary test conf!: " + TEST_CONF + '\n' + str(exio))
    USE_TEST_CONF = False

# create a valid switch manually
# (can be accessed from any test as an example of a non-parsed, valid switch)
switch1 = wpswitch.switch(
    'test_switches_target.txt',
    'testmanualswitch',
    ('True', 'False'),
    'testswitch =',
    'a test switch')

# Test Cases


class test_wpswitch(unittest.TestCase):

    def setUp(self):
        """ setup the test, creates a temporary switches.conf """

        if USE_TEST_CONF:
            try:
                with open(TEST_CONF, 'w') as ftestconf:
                    ftestconf.write(test_data_local)
                    self.created_test_conf = True
                    # print "setUp: created test conf: " + TEST_CONF
            except (Exception, OSError, IOError) as exio:
                print("setUp: cannot create test conf!: " + TEST_CONF + '\n' + str(exio))
                self.created_test_conf = False

        # Load switches for these tests to use (also tests whether they can be loaded)
        self.switches = wpswitch.read_lines(test_lines_local)
        self.assertIsNotNone(self.switches,
                             msg="testCanLoadList: read_lines() returned None")
        self.assertNotEqual(self.switches, [],
                            msg="testCanLoadList: read_lines() returned empty list for test data")

    def tearDown(self):
        """ tear down the test, remove temporary switches.conf if needed. """

        # remove temporary switches.conf
        if self.created_test_conf:
            try:
                os.remove(TEST_CONF)
                #print("tearDown: removed test conf: " + TEST_CONF)
            except (Exception, OSError, IOError) as exio:
                print("tearDown: cannot remove temporary switches.conf!: " + TEST_CONF + '\n' + str(exio))
        else:
            print("tearDown: self.created_test_conf = False, no file will be removed.")

    def testParseDataEqualsSwitchStr(self):
        """ ....parse_switchdata() should create a valid switch from a get_switch_str() """
        switch2 = wpswitch.parse_switchdata(switch1.get_switch_str())
        self.assertIsNotNone(switch2,
                             msg="parse_switchdata() failed parsing get_switch_str()")
        self.assertEqual(switch1, switch2,
                         msg="parse_switchdata() incorrectly parsed get_switch_str()")
        self.assertEqual(switch1.get_switch_str(), switch2.get_switch_str(),
                         msg="parsed switch data created unequal switch string")

    def testCanLoadList(self):
        """ ....load switches from lines of strings. """

        self.switches = wpswitch.read_lines(test_lines_local)
        self.assertIsNotNone(self.switches,
                             msg="testCanLoadList: read_lines() returned None")
        self.assertNotEqual(self.switches, [],
                            msg="testCanLoadList: read_lines() returned empty list for test data")

    @unittest.skipIf(not USE_TEST_CONF, "no test file to use")
    def testCanLoadFile(self):
        """ ....loads switches from a file """

        self.assertEqual(self.created_test_conf, True,
                         msg="testCanLoadFile: setUp did not create test switches.conf")

        self.switches = wpswitch.read_file(TEST_CONF)
        self.assertIsNotNone(self.switches,
                             msg="testCanLoadFile: read_file() returned None")
        self.assertNotEqual(self.switches, [],
                            msg="testCanLoadFile: read_file() returned empty list for test file")

    def testFindSwitchIsRegEx(self):
        """ ....find regex test switch by name, is_regex() should return True """

        #switches = wpswitch.read_lines(test_lines_local)
        self.assertIsNotNone(self.switches,
                             msg="testFindSwitchIsRegEx: switches is None, could not read_lines()")
        self.assertNotEqual(self.switches, [],
                            msg="testFindSwitchIsRegEx: switches is empty, read_lines() failed")
        regexswitch = wpswitch.get_switch_byname('testswitchregex', self.switches)
        self.assertIsNotNone(regexswitch,
                             msg="get_switch_byname(testswitchregex, switches) returned None")
        self.assertEqual(regexswitch.is_regex(), True,
                         msg="regexswitch.is_regex() returned False for: " + regexswitch.get_switch_str())

    def testCanHandleGroups(self):
        """ ....retrieves all group names """

        #switches = wpswitch.read_lines(test_lines_local)
        self.assertIsNotNone(self.switches,
                             msg="self.switches is None, could not read_lines()")
        self.assertNotEqual(self.switches, [],
                            msg="self.switches is empty, read_lines() failed")
        # gather all groups from switch list
        groupnames = wpswitch.get_groups(self.switches)
        # make sure they are both tuple lists, because [] != ()
        test_groupnames = sorted(groupnames)
        test_expectednames = sorted(list(GROUP_MEMBERS.keys()))
        # test equality, print results on failure
        self.assertEqual(test_groupnames, test_expectednames,
                         msg="switch group names did not match expected groups:\n" +
                             '    expected:\n        ' + '\n        '.join(test_expectednames) + '\n\n' +
                             '      actual:\n        ' + '\n        '.join(test_groupnames) + '\n')

        # test group members
        for name in groupnames:
            # get expected members of group name.
            expected_members = GROUP_MEMBERS[name]
            # incase someone messed up the expected members, None should be [].
            if expected_members is None:
                expected_members = []
            # get names of actual members (get_group_members() actually returns switch() objects.
            actual_members = [s.name for s in wpswitch.get_group_members(name, self.switches)]
            # test equality of expected/actual members, print results on failure.
            self.assertEqual(expected_members, actual_members,
                             msg="group members did not match the expected members:\n" +
                                 '    expected:\n        ' + ('\n        ' + name + ': ').join(expected_members) + '\n' +
                                 '      actual:\n        ' + ('\n        ' + name + ': ').join(actual_members) + '\n')

    def testCanGetGroupNameByList(self):
        """ ....retrieves a group name from a list of switches """

        #switches = wpswitch.read_lines(test_lines_local)
        self.assertIsNotNone(self.switches,
                             msg="testCanGetGroupNameByList: switches is None, read_lines() failed.")
        self.assertNotEqual(self.switches, [],
                            msg="testCanGetGroupNameByList: switches is [], read_lines() failed.")
        # select the last group in expected group data (the first is None, which might not help)
        testgroupname = list(GROUP_MEMBERS.keys())[-1]
        groupmembers = wpswitch.get_group_members(testgroupname, self.switches)
        self.assertIsNotNone(groupmembers,
                             msg="testCanGetGroupNameByList: get_group_members(" + testgroupname + ')' +
                                 " returned None")
        self.assertNotEqual(groupmembers, [],
                            msg="testCanGetGroupNameFromList: get_group_members(" + testgroupname + ')' +
                            " returned []")

        # test that get_group_bylist() works correctly.
        getgroupname = wpswitch.get_group_bylist(groupmembers)
        self.assertEqual(testgroupname, getgroupname,
                         msg='testCanGetGroupNameFromList: get_group_bylist() failed!\n    ' +
                             '    expecting: ' + testgroupname + '\n' +
                             '       actual: ' + getgroupname + '\n')

    def testBadSwitchDataCaught(self):
        """ ....bad switch data returns None, empty desc is not bad data. """

        # incomplete
        baddata = "filename|name|"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNone(badswitch,
                          msg="parse_switchdata() did not return None on bad data: " + baddata)
        # empty values
        baddata = "filename|name||finder|desc"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNone(badswitch,
                          msg="parse_switchdata() did not return None on bad data: " + baddata)
        # not enough possible values
        baddata = "filename|name|value1|finder"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNone(badswitch,
                          msg="parse_switchdata() did not return None on bad data: " + baddata)
        # too many possible values
        baddata = "filename|name|val1,val2,val3|finder"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNone(badswitch,
                          msg="parse_switchdata() did not return None on bad data: " + baddata)
        # empty description (should not return None)
        baddata = "filename|name|val1,val2|finder|"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNotNone(badswitch,
                             msg="parse_switchdata() returned None on empty desc: " + baddata)

        # extra | chars (should not return None)
        baddata = "|filename|name|val1,val2|finder|desc|"
        badswitch = wpswitch.parse_switchdata(baddata)
        self.assertIsNotNone(badswitch,
                             msg="parse_switchdata() returned None on extra leading | chars: " + baddata)

# START OF SCRIPT
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    testprogram = unittest.main(exit=False, verbosity=2)
    results = testprogram.result
    # show skipped tests.
    if len(results.skipped) > 0:
        print("some tests were skipped!:")
        for test, reason in results.skipped:
            if ' ' in str(test):
                testname = str(test).split(' ')[0]
            else:
                testname = str(test)
            print('    ' + testname + ": " + reason)
