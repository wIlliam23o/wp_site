""" Welborn Productions - Utilities - Tests
    Tests for the utilities module.
    -Christopher Welborn 2-4-15
"""

from django.conf import settings
from django.test import TestCase

from wp_main.utilities import utilities as utils


class UtilTest(TestCase):

    def test_append_path(self):
        """ append_path() build unix paths correctly. """
        # Common use case.
        self.assertEqual(
            'home/fake',
            utils.append_path('home', '/fake'),
            msg='basic case is broken.'
        )
        # Double /'s
        self.assertEqual(
            '/home/fake',
            utils.append_path('/home/', '/fake'),
            msg='double /\'s is broken.'
        )
        # Multiple /'s
        self.assertEqual(
            '/home/fake/dir',
            utils.append_path('//home/', '/fake//', '//dir///'),
            msg='failed to trim extra /\'s.'
        )

    def test_get_absolute_path(self):
        """ get_absolute_path() returns only static directories, with no '..'.
        """
        # Common case.
        self.assertEqual(
            '{}/css/main.min.css'.format(settings.STATIC_ROOT),
            utils.get_absolute_path('/static/css/main.min.css'),
            msg='failed to get absolute path for known file.'
        )

        # Guard against '..' tricks.
        self.assertEqual(
            '',
            utils.get_absolute_path('/static/../html/index.html'),
            msg='failed to guard against \'..\'!'
        )

        # Guard against non-static files.
        self.assertEqual(
            '',
            utils.get_absolute_path('{}/wp_main'.format(
                settings.BASE_PARENT
            )),
            msg='failed to guard against non-static file!'
        )

        # Guard against multiple //.
        self.assertEqual(
            '{}/css/main.min.css'.format(settings.STATIC_ROOT),
            utils.get_absolute_path('///static//css/main.min.css'),
            msg='failed to fix slightly malformed url.'
        )

    def test_get_filename(self):
        """ get_filename() returns base file name correctly. """
        # Common use case.
        self.assertEqual(
            'filename.txt',
            utils.get_filename('/dir/path/filename.txt'),
            msg='base file name is incorrect.')
        # Incompatible arguments for os.path.split should return the arg back.
        self.assertEqual(
            None,
            utils.get_filename(None),
            msg='None arg doesn\'t return None.')

    def test_get_relative_path(self):
        """ get_relative_path() returns a valid relative path. """

        # Guard against '..'.
        self.assertEqual(
            '',
            utils.get_relative_path('{}/../html'),
            msg='failed to guard against ..!'
        )

        # Valid static path.
        self.assertEqual(
            '/static/css/main.min.css',
            utils.get_relative_path('{}/css/main.min.css'.format(
                settings.STATIC_ROOT
            )),
            msg='failed to get get relative path.'
        )

        # Valid base path.
        self.assertEqual(
            '/wp_main',
            utils.get_relative_path('{}/wp_main'.format(
                settings.BASE_PARENT
            )),
            msg='failed to get relative base path.'
        )

    def test_remove_list_dupes(self):
        """ remove_list_dupes() removes duplicates from list and tuples. """
        self.assertIsInstance(
            utils.remove_list_dupes([1, 1, 2, 4]),
            list,
            msg='received a list and returned something else.')

        self.assertIsInstance(
            utils.remove_list_dupes((1, 1, 2, 4)),
            tuple,
            msg='received a tuple and returned something else.')

        self.assertEqual(
            (1, 2, 4),
            utils.remove_list_dupes((1, 1, 2, 4)),
            msg='did not remove duplicates from the tuple.')
        self.assertEqual(
            [1, 2, 4],
            utils.remove_list_dupes([1, 1, 2, 4]),
            msg='did not remove duplicates from the list.')

        self.assertEqual(
            [1, 1, 2, 2, 3, 3, 4, 4],
            utils.remove_list_dupes(
                (1, 1, 2, 2, 3, 3, 3, 4, 4, 4), max_allowed=2),
            msg='max_allowed returned incorrect amount.')

    def test_slice_list(self):
        """ slice_list() returns correct items with and without max_items. """
        lst = list(range(50))
        self.assertEqual(
            25,
            len(utils.slice_list(lst, max_items=25)),
            msg='incorrect length when max_items is used.')

        self.assertEqual(
            [5, 6, 7, 8, 9, 10],
            utils.slice_list(lst, start=5, max_items=6),
            msg='incorrectly sliced with max_items.')

        self.assertEqual(
            [47, 48, 49],
            utils.slice_list(lst, start=47),
            msg='incorrectly slice without max_items.')

    def test_trim_special(self):
        """ trim_special() trims dangerous characters from a string. """
        bad = '<script src="http://domain.com/file.js"></script>'
        expected = 'script srchttpdomaincomfilejsscript'
        self.assertEqual(
            expected,
            utils.trim_special(bad),
            msg='did not trim correctly.'
        )

        self.assertEqual(
            None,
            utils.trim_special(None),
            msg='did not return original falsey argument.')

        with self.assertRaises(TypeError):
            utils.trim_special(1)
