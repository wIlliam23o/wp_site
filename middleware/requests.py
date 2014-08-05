""" Welborn Productions - MiddleWare - Requests
    Handles requests coming in to welbornprod.
"""

from os.path import isfile
import re

from django.conf import settings
from django.http import HttpResponse

from wp_main.utilities.wp_logging import logger
_log = logger('middleware.requests').log


def get_remote_host(request):
    """ Returns the HTTP_HOST for this user.
        Arguments:
            request  : The request object to gather info from.
    """
    try:
        host = request.META.get('REMOTE_HOST', None)
    except Exception as ex:
        _log.error('Unable to get remote host:\n{}'.format(ex))
        return None
    return host


def get_remote_ip(request):
    """ Just returns the IP for this user.
        Arguments:
            request  : The request object to gather info from.
    """
    try:
        # possible ip forwarding, if available use it.
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
        if x_forwarded_for:
            remote_addr = x_forwarded_for.split(',')[0].strip()
        else:
            remote_addr = request.META.get('REMOTE_ADDR', None)
    except Exception as ex:
        _log.error('Unable to retrieve remote ip:\n{}'.format(ex))
        return None

    return remote_addr


class WpBanIpMiddleware(object):

    def __init__(self):
        self.configfile = settings.SECRET_BAN_FILE
        # Raw config lines (minus comments/blanks)
        self.configraw = []
        # Compiled regex patterns (after successful file load/parse)
        self.banpatterns = []
        self.log = logger('middleware.requests.wpbanip').log
        if isfile(self.configfile):
            self.parse_config()

    def build_patterns(self):
        """ Build self.banpatterns (compiled regex) list,
            if self.configraw is available.
        """
        if not self.configraw:
            return None

        self.banpatterns = [p for p in self.iter_compile() if p]
        if self.banpatterns:
            banlen = len(self.banpatterns)
            ipstr = 'IP is' if banlen == 1 else 'IPs are'
            self.log.debug('{} {} in the banned list.'.format(banlen, ipstr))
        else:
            self.log.debug('No IPs are in the ban list.')

    def iter_compile(self):
        """ Iterate over self.configraw,
            yielding a <RegEx Pattern> on successful compile,
            or None on failure.
        """

        for configpat in self.configraw:
            pat = self.try_compile(configpat)
            yield pat if pat else None

    def parse_config(self):
        """ Parse the config file contents, if available.
            Logs errors, sets:
                self.banpatterns (via self.build_patterns())
        """
        self.configraw = []
        try:
            with open(self.configfile) as f:
                for line in f:
                    linetrim = line.strip()
                    if linetrim and (not linetrim.startswith('#')):
                        self.configraw.append(linetrim)
        except EnvironmentError as exread:
            self.log.error('Unable to read ban config:'
                           '{}\n{}'.format(self.configfile, exread))
        else:
            # Successful read, build all of the regex patterns.
            self.build_patterns()

    def process_request(self, request):
        """ Process the incoming request,
            returns a 403 (Permission  Denied) if the user's ip is in the
            banned list.
        """
        # Get remote ip and check for ban patterns.
        remote_ip = get_remote_ip(request)
        if not (self.banpatterns and remote_ip):
            return None

        # We have ban patterns, and a remote ip. Cross-check them,
        # and raise a 403 if one matches.
        for banpat in self.banpatterns:
            if banpat.match(remote_ip):
                # Return the most basic 403 possible.
                # Nothing fancy for people I don't even want on my site.
                return HttpResponse('Forbidden.',
                                    content_type='text/plain',
                                    status=403,
                                    reason='Invalid Permissions')

        # Success.
        return None

    def try_compile(self, repatstr):
        """ Try compiling a regex pattern string,
            Errors are logged,
            Returns a <RegEx Pattern> object on success,
            Returns None on failure.
        """
        try:
            repat = re.compile(repatstr)
        except Exception as exre:
            self.log.error('Bad regex pattern: {}\n{}'.format(repatstr, exre))
            return None
        return repat
