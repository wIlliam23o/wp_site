from django.test import TestCase

from wp_main.utilities import responses as resp


class ResponsesTest(TestCase):

    def test_get_request_arg(self):
        """ get_request_arg retrieves and converts the proper types. """
        req = FakeRequestArgs(
            request={
                'id': '5',
                'start': '99999998',
                'end': '-1'
                })

        self.assertEqual(
            type(5),
            type(resp.get_request_arg(req, 'id')),
            msg='Types are mismatched for get_request_arg!'
        )

        self.assertEqual(
            6,
            resp.get_request_arg(req, 'start', max_val=6),
            msg='Request arg was not clamped by max_val!'
        )

        self.assertEqual(
            0,
            resp.get_request_arg(req, 'end', min_val=0),
            msg='Request arg was not clamped by min_val!'
        )

        self.assertEqual(
            5,
            resp.get_request_arg(req, ('i', 'nonexistent', 'id'), default=0),
            msg='Aliased request arg was not picked up: id'
        )

        self.assertIsNone(
            resp.get_request_arg(req, 'nonexistent'),
            msg='Non existent request arg did not return None.'
        )

        self.assertEqual(
            26,
            resp.get_request_arg(req, 'nonexistent', default=26),
            msg='Non existent request arg did not return the default: 26'
        )


class FakeRequestArgs(object):
    """ For testing functions that deal with request args.
        Ensured to have at least an empty REQUEST, GET, and POST attribute.
    """
    def __init__(self, request=None, get=None, post=None):
        self.REQUEST = request or {}
        self.GET = get or {}
        self.POST = post or {}
