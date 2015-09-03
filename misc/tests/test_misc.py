""" Welborn Productions - Misc - Tests
    Tests the wp_misc model and misctools.
    -Christopher Welborn 2-4-15
"""
from django.test import TestCase
from misc.types import MiscTypes, Lang
from misc.models import wp_misc


class MiscTestCase(TestCase):

    def setUp(self):  # noqa
        """ Setup tests, create a basic misc object. """

        wp_misc.objects.create(
            filetype=MiscTypes.script,
            language=Lang.python2,
            name='testmiscscript',
            filename='/static/files/misc/testscript.py',
            description='Test script for misc objects.')

    def test_basic_load(self):
        """ Test that a misc object can be loaded """

        mo = wp_misc.objects.get(name='testmiscscript')
        self.assertIsNotNone(
            mo,
            msg='Basic wp_misc.objects.get() returned None!')
