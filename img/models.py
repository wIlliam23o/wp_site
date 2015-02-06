""" Welborn Productions - img - Models
    Holds various models for uploading/viewing images shared with the img app.
    -Christopher Welborn 2-2-15
"""
import logging
from datetime import datetime

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from wp_main.utilities import id_tools
log = logging.getLogger('wp.img.models')


class wp_image(models.Model):  # noqa

    """ Holds information about an uploaded image via the 'img' app. """
    # Image file.
    image = models.FileField(
        'image',
        blank=False,
        upload_to='img',
        help_text='The file for the image.')

    # Human-readable image id (generated on save).
    image_id = models.CharField(
        'image id',
        max_length=255,
        db_index=True,
        blank=True,
        help_text='Image ID for building urls.')

    # File name, saved as a convenience for searching.
    filename = models.CharField(
        'file name',
        max_length=1024,
        db_index=True,
        blank=True,
        default='',
        help_text='File name for this image, read only.')

    # Publish date.
    publish_date = models.DateTimeField(
        'publish date',
        blank=False,
        default=datetime.now,
        help_text='When the image was uploaded.')

    # Image Width (in pixels)
    height = models.IntegerField(
        'height',
        blank=True,
        default=0,
        help_text='The height for the image.')

    # Image Width (in pixels)
    width = models.IntegerField(
        'width',
        blank=True,
        default=0,
        help_text='The width for the image.')

    # Image album (for folder-like behavior)
    album = models.CharField(
        'album',
        blank=True,
        default='',
        max_length=255,
        help_text='Album name for this image.')

    # Image title.
    title = models.CharField(
        'title',
        blank=True,
        default='',
        max_length=255,
        help_text='Title for the image.')

    # Description text for this image.
    description = models.TextField(
        'description',
        blank=False,
        help_text='Description for this image.')

    # Disabled image? (won't show in listings.)
    disabled = models.BooleanField(
        'disabled',
        default=False,
        help_text='Whether or not this image is listable.')

    # Private image? (won't show in public listings.)
    private = models.BooleanField(
        'private',
        default=False,
        help_text='Whether or not this image is private (not listable).')

    # Download count for the image.
    download_count = models.IntegerField(
        'download count',
        default=0,
        help_text='How many times this image has been downloaded.')

    # View count for the image.
    view_count = models.IntegerField(
        'view count',
        default=0,
        help_text='How many times this image has been viewed.')

    date_hierarchy = 'publish_date'

    class Meta:
        get_latest_by = 'publish_date'
        db_table = 'wp_images'
        ordering = ['-publish_date']
        verbose_name = 'Image'
        verbose_name_plural = 'Images'

    def __str__(self):
        """ Default string format for an image object.
            This is a simple format.
        """
        if hasattr(self, 'id'):
            _id = self.id
            basestr = '{}: ({})'.format(_id, self.image_id)
        else:
            basestr = '({})'.format(self.image_id)
        title = self.title or 'Untitled'
        finalstr = '{} {} - {}'.format(basestr, self.image.name, title)
        if len(finalstr) > 80:
            return finalstr[:80]
        return finalstr

    def save(self, *args, **kwargs):
        """ Generate image_id before saving. """
        if (not self.filename) and self.image:
            self.filename = self.image.name
            log.debug('Saved with filename: {}'.format(self.filename))
        super(wp_image, self).save(*args, **kwargs)
        # Generate a image_id for this image if it doesnt have one already.
        if not self.image_id:
            self.generate_id()
        # Save the filename for this image.
        if not self.filename:
            self.update_filename()
        # TODO: Generate self.width and self.height.

    def generate_id(self):
        """ Get current image_id, or generate a new one and saves it. """
        if self.image_id:
            return self.image_id

        realid = getattr(self, 'id', None)
        if realid is None:
            # This will call generate_id() again, but make an id to use.
            self.save()

        newid = id_tools.encode_id(realid)
        self.image_id = newid
        # Save the newly generated id.
        self.save()

    def get_url(self):
        """ Return absolute url.
            *Reverse url lookup really needs to be used here.
        """
        return '/media/?id={}'.format(self.image_id)

    def reverse_id(self, imageid=None):
        """ Decode a image_id, return the actual id.
            If no image_id is given, it decodes the current images id.
        """
        if imageid is None:
            if not self.image_id:
                return None
            return id_tools.decode_id(self.image_id)
        # Decode imageid given..
        return id_tools.decode_id(imageid)

    def update_filename(self):
        """ Updates the .filename attribute based on image.name. """
        if not self.image:
            return None
        if self.filename == self.image.name:
            return None

        self.filename = self.image.name
        # This will call update_filename() again, but do nothing.
        self.save()
        log.debug('Updated filename: {}'.format(self.filename))


@receiver(pre_delete, sender=wp_image)
def wp_image_delete(sender, instance, **kwargs):
    """ Delete the file along with the instance. """
    if instance.image:
        # Don't try to save a dying model.
        try:
            instance.image.delete(save=False)
        except EnvironmentError as ex:
            imgname = getattr(instance.image, 'name', '')
            if not imgname:
                imgname = repr(instance.image)
            log.error('Unable to delete image: {}\n{}'.format(imgname, ex))
