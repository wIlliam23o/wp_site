from django.db import models
from datetime import datetime
from random import SystemRandom

from wp_main.utilities.wp_logging import logger
_log = logger('apps.paste.models').log

IDCHOICES = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
SYSRANDOM = SystemRandom()
IDSTARTCHAR = 'a'
IDPADCHARS = ('x', 'y', 'z')


def generate_random_id(length=4):
    """ Generate a random/unique id for a paste. """
    finalid = [SYSRANDOM.choice(IDCHOICES) for i in range(length)]
    return ''.join(finalid)


def encode_id(realid):
    """ A form of encoding, that is reversible. """
    startchar = ord(IDSTARTCHAR)
    
    finalid = []
    for c in str(realid):
        newchar = chr(startchar + int(c))
        finalid.append(newchar)
    while len(finalid) < 4:
        finalid.append(SYSRANDOM.choice(IDPADCHARS))
    return ''.join(finalid)


def decode_id(idstr):
    """ Decode an id that has been encoded. """
    startchar = ord(IDSTARTCHAR)
    finalid = []
    for c in idstr:
        if c in IDPADCHARS:
            continue
        intstr = str(ord(c) - startchar)
        finalid.append(intstr)
    return int(''.join(finalid))


def repr_header():
    """ Return a string header for the repr(paste) data. """
    return 'publish date        views  id       status   author     title'


class wp_paste(models.Model):

    """ A Paste object for the paste app. """

    # author of the paste.
    author = models.CharField('author',
                              blank=True,
                              default='',
                              max_length=255,
                              help_text='Author for the paste.')

    # author's ip address. (for tracking public submits.)
    author_ip = models.CharField('author\'s ip',
                                 blank=True,
                                 default='',
                                 max_length=15,
                                 help_text='Author\'s IP for the paste.')

    # paste content (can't be blank.)
    content = models.TextField('content',
                               blank=False,
                               help_text='Content for the paste.')

    # paste title..
    title = models.CharField('title',
                             blank=True,
                             default='',
                             max_length=255,
                             help_text='Title for the paste.')

    # language for the paste.
    language = models.CharField('language',
                                blank=True,
                                default='',
                                max_length=255,
                                help_text='Language for highlighting.')

    # Human-readable paste id.
    paste_id = models.CharField('paste id',
                                max_length=255,
                                blank=True,
                                help_text='Paste ID for building urls.')

    # publish date (for sort-order mainly)
    publish_date = models.DateTimeField('publish date',
                                        blank=False,
                                        default=datetime.now,
                                        help_text=('Date the paste was '
                                                   'published. '
                                                   '(Set automatically)'))
    
    # api submitted? (True if the paste was submitted through the public api)
    apisubmit = models.BooleanField('api submitted',
                                    default=False,
                                    help_text=('Whether or not this was '
                                               'submitted with the public '
                                               'api.'))

    # disables paste (instead of deleting it, it simply won't be viewed)
    disabled = models.BooleanField('disabled',
                                   default=False,
                                   help_text=('Whether or not this paste is '
                                              'disabled (not viewable).'))
    
    # hold on to the paste forever?
    onhold = models.BooleanField('on hold',
                                 default=False,
                                 help_text=('Whether or not this paste is '
                                            'on hold (never expires).'))

    # private paste? (won't show in public listings.)
    private = models.BooleanField('private',
                                  default=False,
                                  help_text=('Whether or not this paste is '
                                             'private (not listable).'))

    # count of views/downloads
    view_count = models.PositiveIntegerField('view count',
                                             default=0,
                                             help_text=('How many times this '
                                                        'paste has been '
                                                        'viewed.'))
    
    # parent/replyto paste object.
    parent = models.ForeignKey('self',
                               verbose_name='parent of this paste',
                               blank=True,
                               null=True,
                               related_name='children')

    date_hierarchy = 'publish_date'

    def __str__(self):
        """ Default string format for a paste object.
            This is a simple format, for more info see: __repr__
        """
        if hasattr(self, 'id'):
            _id = self.id
            basestr = '{}: ({})'.format(_id, self.paste_id)
        else:
            basestr = '({})'.format(self.paste_id)
        finalstr = '{} {}'.format(basestr, self.title)
        if len(finalstr) > 80:
            return finalstr[:80]
        return finalstr
    
    def __repr__(self):
        """ Format a paste for printing (different from str(paste))
            This provides:
                publish_date, view count, paste_id, enabled, and title
        """
        datestr = self.publish_date.strftime('%m-%d-%Y %I:%M:%S')
        viewstr = '({})'.format(self.view_count).ljust(6)
        idstr = self.paste_id or 'new'
        idstr = idstr.ljust(8)
        statusstr = '[d]' if self.disabled else '[e]'
        statusstr = statusstr.ljust(8)
        authorstr = self.author or '<none>'
        authorstr = authorstr.ljust(10)

        pfmt = '{date} {views} {pasteid} {status} {author} {title}'
        pfmtargs = {
            'date': datestr,
            'views': viewstr,
            'pasteid': idstr,
            'status': statusstr,
            'author': authorstr,
            'title': self.title,
        }
        return pfmt.format(**pfmtargs)
    
    # Meta info for the admin site
    class Meta:
        get_latest_by = 'publish_date'
        db_table = 'wp_pastes'
        ordering = ['-publish_date']
        verbose_name = 'Paste'
        verbose_name_plural = 'Pastes'

    def save(self, *args, **kwargs):
        """ Generate paste_id before saving. """

        super(wp_paste, self).save(*args, **kwargs)
        # Generate a paste_id for this paste if it doesnt have one already.
        if not self.paste_id:
            self.generate_id()

    def generate_id(self):
        """ Get current paste_id, or generate a new one and saves it. """
        if self.paste_id:
            return self.paste_id

        realid = self.id
        if realid is None:
            # This will call generate_id() again, but make an id to use.
            self.save()

        newid = encode_id(realid)
        self.paste_id = newid
        # Save the newly generated id.
        self.save()

    def get_url(self):
        """ Return absolute url.
            reverse url lookup really needs to be used here.
        """
        return '/paste/?id={}'.format(self.paste_id)

    def is_expired(self):
        """ Determine if this paste is expired.
            Pastes that are on hold will never expire.
        """
        if self.onhold:
            return False
        try:
            elapsed = datetime.today() - self.publish_date
        except Exception as ex:
            _log.error('Error getting elapsed time:\n{}'.format(ex))
            return False
        return (elapsed.days > 0)

    def reverse_id(self, pasteid=None):
        """ Decode a paste_id, return the actual id.
            If no paste_id is given, it decodes the current pastes id.
        """
        if pasteid is None:
            if not self.paste_id:
                return None
            return decode_id(self.paste_id)
        # Decode pasteid given..
        return decode_id(pasteid)
