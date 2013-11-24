"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from misc.tools import MiscTypes, Lang
from misc.models import wp_misc


class MiscTestCase(TestCase):

    def setUp(self):
        """ Setup tests, create a basic misc object. """

        wp_misc.objects.create(type=MiscTypes.script,
                               language=Lang.python2,
                               name='testmiscscript',
                               file='/static/files/misc/testscript.py',
                               description='Test script for misc objects.')

    def test_basic_load(self):
        """ Test that a misc object can be loaded """

        mo = wp_misc.objects.get(name='testmiscscript')
        self.assertIsNotNone(mo,
                             msg='Basic wp_misc.objects.get() returned None!')
