from django.db import models

from solo.models import SingletonModel


class home_config(SingletonModel):

    """ Holds basic config for the home/landing page. """

    featured_project = models.ForeignKey(
        'projects.wp_project',
        # Disable backwards relation from projects to here.
        related_name='+',
        # Only allow enabled projects.
        limit_choices_to={'disabled': False},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Featured project for the landing page.')

    featured_app = models.ForeignKey(
        'apps.wp_app',
        # Disable backwards relation from apps to here.
        related_name='+',
        # Only allow enabled apps.
        limit_choices_to={'disabled': False},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Featured web app for the landing page.')

    featured_blog = models.ForeignKey(
        'blogger.wp_blog',
        related_name='+',
        limit_choices_to={'disabled': False},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Featured blog post (latest is used if none is set.)')

    show_latest_tweet = models.BooleanField(
        'show latest tweet',
        default=True,
        help_text='Whether or not to retrieve and show your latest tweet.')

    welcome_message = models.TextField(
        'welcome message',
        blank=True,
        default='',
        help_text='Extra welcome message to show.')

    class Meta:
        verbose_name = 'Home Configuration'
        verbose_name_plural = 'Home Configuration'
        db_table = 'home_config'
