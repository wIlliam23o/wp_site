from django.db import models
from misc.types import MiscTypes, Lang
from datetime import date

# Module level functions...


class wp_misc(models.Model):  # noqa

    """ Model for a misc object,
        small snippets of code, small scripts, text, etc. """
    # Proper Name for this object (must be unique because .get(name=) is used
    name = models.CharField(
        blank=False,
        max_length=250,
        help_text='Name for this misc object (must be unique)'
    )

    # Alias for this object (usually name.lower().replace(' ', ''),
    # used for building urls)
    # Prepopulated using Django admin in the fashion described above.
    alias = models.CharField(
        blank=False,
        max_length=250,
        help_text='Alias for this misc object (used for building urls)'
    )

    # short description of misc object
    # (longer description should be in it's htmlcontent/content)
    description = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        help_text='Short description for the misc object.'
    )

    # version in the form of X.X.X or XX.XX.XX
    version = models.CharField(
        blank=True,
        default='1.0.0',
        max_length=120,
        help_text='Version string in the form of X.X.X'
    )

    # filename for this misc object.
    # used for viewing/downloading
    filename = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=(
            'Main source file for the misc object for viewing/downloading.'
        )
    )

    # Html content (for long description of this misc object)
    # If no Html file is present, then contents is used.
    contentfile = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=(
            'Html file for this misc object, used for long description.'
        )
    )

    # Content (for long description of this misc object)
    content = models.TextField(
        blank=True,
        default='',
        help_text=' '.join((
            'Content for this misc object (long desc)',
            'if contentfile is not used.'
        ))
    )

    # usage string for scripts. (raw usage string, no html)
    usage_string = models.TextField(
        blank=True,
        default='',
        max_length=5000,
        help_text=' '.join((
            'Usage string if this is a full script with cmdline options.',
            '(no html allowed)'
        ))
    )

    # misc type (code file, snippet, text, script, archive, executable, etc.)
    filetype = models.CharField(
        blank=False,
        default='None',
        max_length=100,
        choices=MiscTypes.fieldchoices,
        help_text='Type of misc object (snippet, code, archive, text, etc.)'
    )

    # language type for this misc object
    # (can be None, Python, Python2, Python3, Bash, C, etc.)
    language = models.CharField(
        blank=False,
        default='None',
        max_length=100,
        choices=Lang.fieldchoices,
        help_text=' '.join((
            'Programming language for this misc object',
            '(None, Python, C, Bash, etc.)'
        ))
    )

    # disables project (instead of deleting it, it simply won't be viewed)
    disabled = models.BooleanField(default=False)

    # count of views/downloads
    view_count = models.IntegerField(
        default=0,
        help_text=(
            'How many times this misc object has been viewed. (Integer)'
        )
    )
    download_count = models.IntegerField(
        default=0,
        help_text=(
            'How many times this misc object has been downloaded. (Integer)'
        )
    )

    # publish date (for sort-order mainly)
    publish_date = models.DateField(
        blank=False,
        default=date.today,
        help_text=' '.join((
            'Date the misc object was published.',
            '(Automatically set to today.)'
        ))
    )

    # admin stuff
    date_hierarchy = 'publish_date'

    def __str__(self):
        """ stringify this object, with optional version string. """
        s = str(self.name)
        if self.version:
            s = ' '.join((s, 'v. {}'.format(self.version)))
        return s

    def __repr__(self):
        """ same as str() """
        return self.__str__()

    # Meta info for the admin site
    class Meta:
        get_latest_by = 'publish_date'
        ordering = ['name']
        verbose_name = 'Misc. Object'
        verbose_name_plural = 'Misc. Objects'
