from django.db import models
import os.path

# Create your models here.


class file_tracker(models.Model):

    """ holds info about a single file, to better track downloads """

    # Filename info.
    filename = models.CharField(
        max_length=1024,
        blank=False,
        help_text='Filename for the file being tracked. (Absolute path)')
    shortname = models.CharField(
        max_length=512,
        default='',
        blank=True,
        help_text='Short filename for the file (without directory)')
    location = models.CharField(
        max_length=1024,
        default='',
        blank=True,
        help_text=(
            'Convenience attribute, the directory where the file is located.'
        )
    )
    notes = models.TextField(
        default='',
        blank=True,
        help_text='Any notes about the file.')
    # File is related to projects or blog posts?
    project = models.ManyToManyField(
        'projects.wp_project',
        blank=True,
        help_text='One or more wp_projects related to the file.')
    post = models.ManyToManyField(
        'blogger.wp_blog',
        blank=True,
        help_text='One or more wp_blogs related to the file.')

    # General counts
    download_count = models.BigIntegerField(
        default=0,
        help_text='How many times the file has been downloaded. (Integer)')
    view_count = models.BigIntegerField(
        default=0,
        help_text=' '.join((
            'How many times the file has been viewed with \'viewer\'.',
            '(Integer)'
        ))
    )

    def __str__(self):
        return self.get_shortname(dosave=False)

    def __unicode__(self):
        return self.get_shortname(dosave=False)

    def get_shortname(self, updateinfo=False, dosave=False):
        """ retrieves shortname if it is set,
            will set the shortname for you and return it
        """
        if self.filename is None:
            return None

        if (not self.shortname) or (updateinfo):
            # update missing info, or force update.
            self.shortname = os.path.split(self.filename)[1]
            if dosave:
                self.save()
        return self.shortname

    def get_location(self, updateinfo=False, dosave=False):
        """ retrieves dir for this file if it is set,
            will set the location for you and return it
        """
        if self.filename is None:
            return None

        if (not self.location) or (updateinfo):
            # Update missing info, or force update.
            self.location = os.path.split(self.filename)[0]
            if dosave:
                self.save()
        return self.location

    def set_filename(self, newfilename, updateinfo=True, dosave=True):
        """ sets the filename and saves it
            (just like myfile.filename=blah, myfile.save())
        """

        if newfilename is None:
            return None
        self.filename = newfilename
        if updateinfo:
            self.get_location(updateinfo=updateinfo)
            self.get_shortname(updateinfo=updateinfo)
        if dosave:
            self.save()
        return self.filename

    # Meta info for the admin site
    class Meta:
        ordering = ['shortname']
        verbose_name = 'File Tracker'
        verbose_name_plural = 'File Trackers'
