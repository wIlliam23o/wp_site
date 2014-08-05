from django.db import models

from solo.models import SingletonModel


class home_config(SingletonModel):

    """ Holds basic config for the home/landing page. """
    featured_project_alias = models.CharField(
        'featured project alias',
        max_length=255,
        blank=True,
        default='',
        help_text='The alias for a project to be featured.')

    featured_app_alias = models.CharField(
        'featured app alias',
        max_length=255,
        blank=True,
        default='',
        help_text='The alias for a web app to be featured.')

    show_latest_tweet = models.BooleanField(
        'show latest tweet',
        default=True,
        help_text='Whether or not to retrieve and show your latest tweet.')

    class Meta:
        verbose_name = 'Home Configuration'
        verbose_name_plural = 'Home Configuration'
        db_table = 'home_config'
