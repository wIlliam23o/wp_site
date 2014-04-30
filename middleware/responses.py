""" Welborn Productions - MiddleWare - Responses
    Handles responses coming from welbornprod views.
"""

import base64
import re

from wp_main.utilities.wp_logging import logger
_log = logger('middleware.responses').log

# RegEx for finding an email address
# (not compiled, because it gets compiled with additional
#  regex in some functions)
re_email_address = r'[\d\w\-\.]+@[\d\w\-\.]+\.[\w\d\-\.]+'


class WpResponseMiddleware (object):

    """ This does what it is supposed to do (cleans html),
        but it takes forever. It has been disabled for now.
    """

    def __init__(self):
        self.rawbytes = None
        self.text = None
        self.lines = None

    def apply_changes(self, response):
        """ Apply modified WpResponseMiddleware.content to a response. """
        if self.lines is None:
            return False
        self.text = '\n'.join(self.lines)
        if not self.text:
            return False

        # We have final text, encode it and modify the response.
        try:
            encoded = self.text.encode('utf-8')
        except UnicodeEncodeError as exuni:
            _log.error('Error encoding final text:\n{}'.format(exuni))
            return False

        # Encoded all changes, apply it to the original response.
        response.content = encoded
        return True

    def find_email_addresses(self):
        """ finds all instances of email@addresses.com inside a wp-address
            classed tag.
            for hide_email().
        """
        if not self.lines:
            return []

        # regex pattern for locating an email address.
        s_addr = ''.join([r'(<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address',
                          r'[\'"])(.+)?[ >](',
                          re_email_address,
                          ')',
                          ])
        re_pattern = re.compile(s_addr)
        raw_matches = re.findall(re_pattern, '\n'.join(self.lines))
        addresses = []
        for groups in raw_matches:
            # the last item is the address we want
            addresses.append(groups[-1])
        return addresses

    def find_mailtos(self):
        """ finds all instances of:
                <a class='wp-address' href='mailto:email@adress.com'></a>
            for hide_email().
            returns a list of href targets:
                ['mailto:name@test.com', 'mailto:name2@test2.com'],
            returns empty list on failure.

        """
        if not self.lines:
            return []

        # regex pattern for finding href tag with 'mailto:??????'
        # and a wp-address class
        s_mailto = ''.join([r'<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address',
                            r'[\'"][ ]href[ ]?\=[ ]?["\']((mailto:)?',
                            re_email_address,
                            ')',
                            ])
        re_pattern = re.compile(s_mailto)
        raw_matches = re.findall(re_pattern, '\n'.join(self.lines))
        mailtos = []
        for groups in raw_matches:
            # first item is the mailto: line we want.
            mailtos.append(groups[0])
        return mailtos

    def hide_email(self):
        """ base64 encodes all email addresses for use with wptool.js
            reveal functions.
            for spam protection.
            (as long as the email-harvest-bot doesn't decode Base64)
        """

        if not self.lines:
            return False

        # Fix py3 with base64.encodebytes(), encode/decode also added.
        # TODO: Remove the hasattr() when py2 is completely phased out of this.
        if hasattr(base64, 'encodebytes'):
            encode = getattr(base64, 'encodebytes')
        else:
            encode = getattr(base64, 'encodestring')

        final_output = []
        for sline in self.lines:
            mailtos = self.find_mailtos()
            for mailto in mailtos:
                b64_mailto = encode(mailto.encode('utf-8'))
                sline = sline.replace(mailto,
                                      b64_mailto.decode('utf-8').replace('\n', ''))

            emails = self.find_email_addresses()
            for email in emails:
                b64_addr = encode(email.encode('utf-8'))
                sline = sline.replace(email,
                                      b64_addr.decode('utf-8').replace('\n', ''))

            # add line (encoded or not)
            final_output.append(sline)
        self.lines = [l for l in final_output]
        return True

    def is_comment(self, line):
        """ returns true if line is a single-line comment. (html or js) """
        line = line.replace('\t', '').replace(' ', '')
        return ((line.startswith('<!--') and line.endswith('-->')) or
                (line.startswith('/*') and line.endswith('*/')))

    def process_content(self):
        """ Runs all of the modifier functions in proper order. 
            Sets self.finaltext
        """
        success = [
            self.hide_email(),
            self.remove_comments(),
            self.remove_whitespace(),
        ]
        return all(success)

    def process_response(self, request, response):
        """ Process the HttpResponse's content. """
        self.rawbytes = response.content
        try:
            self.lines = self.rawbytes.decode('utf-8').split('\n')
        except UnicodeError as exuni:
            _log.error('Error decoding response content:\n{}'.format(exuni))
            # Nothing else can be done if we have no content to work with.
            return None

        # Run all of the content modifications (only changes self.text)
        self.process_content()

        # Modify the original response to contain all of our changes.
        self.apply_changes(response)
        # Success, return the response so other middleware can have it.
        return response

    def remove_comments(self):
        """ splits source_string by newlines and
            removes any line starting with <!-- and ending with -->.
        """
        if not self.lines:
            return False

        self.lines = [l for l in self.lines if not self.is_comment(l)]

        # Don't return the lines themselves, but whether or not they're truthy.
        return True if self.lines else False

    def remove_whitespace(self):
        """ Removes leading/trailing spaces from self.text.
            Avoids <pre> blocks.
        """
        if not self.lines:
            return False

        # start processing
        in_skipped = False
        final_output = []
        for sline in self.lines:
            sline_lower = sline.lower()
            # start of skipped tag
            if "<pre" in sline_lower:
                in_skipped = True
            # process line.
            if in_skipped:
                # add original line.
                final_output.append(sline)
            else:
                trimmed = sline.strip()
                # no blanks.
                if trimmed:
                    final_output.append(trimmed)
            # end of tag
            if "</pre>" in sline_lower:
                in_skipped = False
        self.lines = [l for l in final_output]
        return True
