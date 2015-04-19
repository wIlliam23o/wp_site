#!/usr/bin/env python3
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from downloads.models import file_tracker


class DownloadsTestCase(TestCase):
    
    def setUp(self):
        """ Setup some basic file trackers to test. """
        
        file_tracker.objects.create(filename='static/testfile.py',
                                    shortname='testfile.py',
                                    location='static',
                                    notes='not a real file, created for downloads.tests...',
                                    download_count=5,
                                    view_count=7)
    
    def create_test_filetracker(self):
        """ Retrieves the test file_tracker from setUp() """
        
        ft = file_tracker.objects.get(shortname='testfile.py')
        self.assertIsNotNone(ft, msg='Test file_tracker (testfile.py) is None!')
        return ft
    
    def test_get_location(self):
        """ file_tracker.get_location() retrieves location """
        
        ft = self.create_test_filetracker()
        
        # blank location, then run get_location()
        ft.location = None
        retrieved_loc = ft.get_location(dosave=True)
        self.assertEqual(retrieved_loc, 'static')
        
        # test that get_location() sets ft.location
        self.assertEqual(ft.location, 'static')
        
    def test_get_shortname(self):
        """ file_tracker.get_shortname() retrieves shortname  """
        
        # retrieve test filetracker
        ft = self.create_test_filetracker()
        # blank shortname, then run 'get_shortname()'.
        # it should retrieve the correct shortname, and assign ft.shortname automatically
        ft.shortname = None
        retrieved_shortname = ft.get_shortname()
        self.assertEqual(retrieved_shortname, 'testfile.py',
                         msg='Getting undefined shortname in get_shortname() did not work!')
        # Make sure ft.shortname was set by get_shortname()
        self.assertEqual(ft.shortname, 'testfile.py',
                         msg='file_tracker.shortname was not set by get_shortname()!')
        
    def test_set_filename(self):
        """ set_filename() sets filename and other info """
        
        # retrieve test filetracker
        ft = self.create_test_filetracker()
        
        # test setting filename only.
        testfile2 = 'static/newdir/testfile2.py'
        ft.set_filename(testfile2)
        self.assertEqual(ft.filename, testfile2)
        
        # test setting filename and updating info.
        testfile3 = 'static/mydir/testfile3.py'

        setname = ft.set_filename(testfile3, updateinfo=True)
        self.assertEqual(setname, testfile3)
        self.assertEqual(setname, ft.filename)
        
        # check shortname
        self.assertEqual(ft.get_shortname(), 'testfile3.py')
        
        # check location
        self.assertEqual(ft.get_location(), 'static/mydir')
