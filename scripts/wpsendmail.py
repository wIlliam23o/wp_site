#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getpass import getpass, GetPassWarning
import os.path
import smtplib
import sys

from docopt import docopt

# py2 compatibility.
try:
    if sys.version[0] == '3':
        input_ = input
    else:
        input_ = raw_input  # noqa
except SyntaxError:
    input_ = input


NAME = 'WpSendmail'
VERSION = '1.2.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(sys.argv[0])[1]

DEFAULTFROM = ('Welborn Productions', 'cj@welbornprod.com')
DEFAULTSUBJECT = 'Message from Welborn Productions'
SERVER = 'smtp.webfaction.com'
PORT = 25

USAGESTR = """{verstr}

    Sends mail from welbornprod.com, default msgs are from cj@welbornprod.com
    Username and password is needed to send messages.

    Usage:
        {script} -h | -v
        {script} TO MSG [-d] [-D] [-f from_address] [-s subject] [-u user]

    Options:
        MSG                     : Message text, or file to read text from.
        TO                      : One or many 'to' addresses.
                                  Separated by a comma.
        -d,--dryrun             : Just show what would've been sent.
        -D,--debug              : Debug mode, prints more information.
        -f addr,--from addr     : From address to use.
                                  Defaults to: {defaultfrom}
        -h,--help               : Show this message.
        -s text,--subject text  : Subject to use in the mail.
                                  Defaults to: {defaultsubject}
        -u user,--user user     : Username for login.
        -v,--version            : Show version.
""".format(verstr=VERSIONSTR,
           script=SCRIPT,
           defaultfrom=DEFAULTFROM[1],
           defaultsubject=DEFAULTSUBJECT)


def main(argd):
    """ main entry-point, expects docopt arg dict. """

    # Parse from/to
    if argd['--from']:
        from_addr = argd['--from']
    else:
        # Format to 'Display Name <address>'
        from_addr = '{} <{}>'.format(DEFAULTFROM[0], DEFAULTFROM[1])

    to_addrs = argd['TO'].split(',')

    if not to_addrs:
        print('\nYou must provide a To address.')
        return 1

    # Parse message
    msgarg = argd['MSG']
    if os.path.exists(msgarg):
        # Get msg from file.
        try:
            with open(msgarg, encoding='utf-8') as fread:
                msg = fread.read()
        except (IOError, OSError) as exio:
            print('\nUnable to open msg file: {}\n{}'.format(msgarg, exio))
            return 1
    else:
        # plain string message.
        msg = msgarg

    # Parse subject
    subject = argd['--subject'] or DEFAULTSUBJECT

    if argd['--dryrun']:
        # Dry run.
        print('Would\'ve sent:')
        print('        To: {}'.format(', '.join(to_addrs)))
        print('      From: {}'.format(from_addr))
        print('   Subject: {}'.format(subject))
        print('       Msg:')
        print(msg)
        print('\nNo mail sent.')
    else:
        # Get login infor for the server.
        # User
        if argd['--user']:
            user = argd['--user']
        else:
            print('Enter login information for: {}'.format(SERVER))
            user = get_input('UserName')
        if not user:
            return 1

        # Pass
        passwd = get_pass()
        if not passwd:
            return 1

        # Build args for send_mail function.
        sendkwargs = {'subject': subject,
                      'debug': argd['--debug'],
                      'username': user,
                      'passwd': passwd,
                      }

        # Try sending the mail.
        try:
            if send_mail_with_header(from_addr, to_addrs, msg, **sendkwargs):
                print('\nMail sent to:\n    '
                      '{}'.format('\n    '.join(to_addrs)))
            else:
                print('\nUnable to send mail.')
        except Exception as ex:
            print('\n{}'.format(ex))
            return 1
        else:
            # success
            return 0


def get_input(query):
    """ use input() to get an answer to a question. """

    if not query.endswith((':', ': ')):
        query = '{}: '.format(query)
    answer = input_(query)
    if not answer.strip():
        return None

    return answer


def get_pass():
    """ Get the login password in a safer manner than input(). """
    try:
        pw = getpass('\nPassword: ')
    except GetPassWarning:
        print('\nError turning echo off. Password would\'ve been displayed.')
        return None
    if not pw:
        print('\nNo password entered, cancelling.')
        return None
    return pw


def send_mail_with_header(sender, receivers, message, **kwargs):
    """ automatically builds the headers needed.
        Arguments:
            sender      : email for the From: portion
            receivers   : single address to send to, or list of addresses.
            message     : message to be sent.

        Keyword Arguments:
            debug       : tell send_mail() to use debug mode.
            passwd      : password for login.
            username    : user name for login.
            subject     : optional subject to be used.
    """

    # Parse kwargs.
    username = kwargs.get('username', None)
    passwd = kwargs.get('passwd', None)
    subject = kwargs.get('subject', '(no subject given)')
    debug = kwargs.get('debug', False)

    build_header = not (("To:" in message) and ("From:" in message))
    if not isinstance(receivers, (list, tuple)):
        receivers = [receivers]
    if subject is None:
        subject = "(no subject given)"

    if build_header:
        if not sender.strip('\n').endswith('>'):
            sender = '<{}>'.format(sender)
        header = ('To:  <{}>\n'.format('>, <'.join(receivers)) +
                  'From: {}\n'.format(sender) +
                  'Subject: {}\n\n'.format(subject))
    else:
        header = ''
    actual_msg = ''.join([header, message])
    if debug:
        print('trying to send:\n{}'.format(actual_msg))

    return send_mail(sender,
                     receivers,
                     actual_msg,
                     username=username,
                     passwd=passwd,
                     debug=debug)


def send_mail(sender, to, message, username=None, passwd=None, debug=False):
    """ send an email using smtp
        receievers can be a single address string,
        or a list of addresses.
    """
    # make sure receivers is a list
    if not isinstance(to, (list, tuple)):
        to = [to]
    # set debug level
    debug_level = 5 if debug else False

    # login and send mail.
    try:

        smtp_ = smtplib.SMTP(SERVER, port=PORT)
        smtp_.set_debuglevel(debug_level)
        smtp_.login(user=username, password=passwd)
    except Exception as ex:
        print('Can\'t login:\n{}'.format(ex))
        raise Exception('Unable to login!')
    else:
        try:
            smtp_.sendmail(sender, to, message)
            smtp_.quit()
        except Exception as ex:
            print('Can\'t send mail:\n{}'.format(ex))
            if (smtp_ is not None) and (hasattr(smtp_, 'quit')):
                smtp_.quit()
            raise Exception('Cannot send mail!')
    return True

# START OF SCRIPT -------------
if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
