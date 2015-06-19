#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getpass import getpass, GetPassWarning
import os.path
import smtplib
import sys

from docopt import docopt

NAME = 'WpSendmail'
VERSION = '1.3.0'
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
        {script} TO [MSG] [-d] [-D] [-f from_address] [-s subject] [-u user]

    Options:
        MSG                     : Message text, or file to read text from.
                                  Uses stdin when not given.
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
""".format(
    verstr=VERSIONSTR,
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

    # Parse message from user arg, file name, or stdin.
    msgarg = argd['MSG'] or read_stdin()
    if len(msgarg) < 256 and os.path.exists(msgarg):
        # Get msg from file.
        try:
            with open(msgarg, encoding='utf-8') as fread:
                msg = fread.read()
        except EnvironmentError as exio:
            print('\nUnable to open msg file: {}\n{}'.format(msgarg, exio))
            return 1
    else:
        # plain string message.
        msg = msgarg

    # Parse subject
    subject = argd['--subject'] or DEFAULTSUBJECT

    # Get login info for the server.
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
    sendkwargs = {
        'subject': subject,
        'debug': argd['--debug'],
        'dryrun': argd['--dryrun'],
        'username': user,
        'passwd': passwd,
    }

    # Try sending the mail.
    try:
        if send_mail_with_header(from_addr, to_addrs, msg, **sendkwargs):
            if not argd['--dryrun']:
                addresses = '\n    '.join(to_addrs)
                print('\nMail sent to:\n    {}'.format(addresses))
        else:
            print('\nUnable to send mail.')
            return 1
    except Exception as ex:
        print('\n{}'.format(ex))
        return 1

    return 0


def get_input(query):
    """ use input() to get an answer to a question. """

    if not query.endswith((':', ': ')):
        query = '{}: '.format(query)
    answer = input(query)
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


def read_stdin():
    """ Read from stdin, but print a helpful message when stdin is a tty. """
    if sys.stdin.isatty():
        print('\nReading from stdin until EOF (Ctrl + D)\n')
    return sys.stdin.read()


def send_mail_with_header(sender, receivers, message, **kwargs):
    """ Automatically builds the headers needed, sends an email.
        Arguments:
            sender      : email for the From: portion
            receivers   : single address to send to, or list of addresses.
            message     : message to be sent.

        Keyword Arguments:
            debug       : tell send_mail() to use debug mode.
            dryrun      : print the final message, do not send anything.
            passwd      : password for login.
            username    : user name for login.
            subject     : optional subject to be used.
    """

    # Parse kwargs.
    username = kwargs.get('username', None)
    passwd = kwargs.get('passwd', None)
    subject = kwargs.get('subject', '(no subject given)')
    debug = kwargs.get('debug', False)
    dryrun = kwargs.get('dryrun', False)

    if not isinstance(receivers, (list, tuple)):
        receivers = [receivers]
    if subject is None:
        subject = 'No subject'

    if (('To:' in message) and ('From:' in message)):
        # This message already contains headers.
        final_msg = message
    else:
        # Build proper email headers.
        if not sender.strip('\n').endswith('>'):
            sender = '<{}>'.format(sender)
        header = '\n'.join((
            'To:  <{recv}>',
            'From: {snd}',
            'Subject: {subj}'
        )).format(
            recv='>, <'.join(receivers),
            snd=sender,
            subj=subject)

        final_msg = '\n\n'.join((header, message))

    if dryrun:
        print('\nWould\'ve sent:\n\n{}'.format(final_msg))
        return True
    elif debug:
        print('Sending:\n\n{}\n'.format(final_msg))

    return send_mail(
        sender,
        receivers,
        final_msg,
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

        mailer = smtplib.SMTP(SERVER, port=PORT)
        mailer.set_debuglevel(debug_level)
        mailer.login(user=username, password=passwd)
    except Exception as ex:
        raise Exception('Unable to login!: {}'.format(ex))
    else:
        try:
            mailer.sendmail(sender, to, message)
            mailer.quit()
        except Exception as ex:
            if (mailer is not None) and (hasattr(mailer, 'quit')):
                mailer.quit()
            raise Exception('Cannot send mail!: {}'.format(ex))
    return True

# START OF SCRIPT -------------
if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
