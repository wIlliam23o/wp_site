""" Welborn Productions - Apps - Model
    Holds basic info about 'mini-webapps' that live under /apps.
    -Christopher Welborn 2013
"""

from django.db import models
# import django.utils #@UnusedImport: utils
import datetime
import json


class wp_app(models.Model):

    """ Holds information about a single wp app. """
    # project name
    name = models.CharField(
        blank=False,
        max_length=100,
        help_text='Name of the app. (Must be unique)')
    # alias for acessing apps by name
    # ...should be lowercase-no-spaces app name
    alias = models.CharField(
        blank=False,
        max_length=100,
        help_text=('Alias for this app (lowercase, used to build urls)'))
    # short description for the app.
    # (longer description should be in an html file)
    description = models.CharField(
        blank=True,
        default='',
        max_length=1048,
        help_text='Short description for the app.')
    # long string description for app. (or use html_url to load from file.)
    longdesc = models.TextField(
        blank=True,
        default='',
        help_text='Long description for the app.')

    # long description for the app.
    # version in the form of X.X.X or XX.X.X
    version = models.CharField(
        blank=True,
        default='1.0.0',
        max_length=120,
        help_text='Version string in the form of X.X.X')
    # url to image file (will be embedded in html)
    logo_url = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=('URL of logo image (possible future development.)'))
    # html file for longer description
    html_url = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=('Html file for this app, containing the long description.'))
     # directory for screenshot images
    screenshot_dir = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=('Directory containing screenshots for the app (relative)'))
    # optional main source file (.py file to view)
    source_file = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=('Main source code file for the app for viewing.'))
    # optional source dir (dir containing source files to view)
    source_dir = models.CharField(
        blank=True,
        default='',
        max_length=512,
        help_text=(
            'Directory containing multiple source code files for viewing.'))
    # publish date (for sort-order mainly)
    publish_date = models.DateField(
        blank=False,
        default=datetime.date.today(),
        help_text=('Date the app was published, automatically set to today.'))

    # disables app (instead of deleting it, it simply won't be viewed)
    disabled = models.BooleanField(default=False)

    # count of views
    view_count = models.IntegerField(
        default=0,
        help_text=('How many times this project has been viewed. (Integer)'))

    # json data
    # can hold any information concerning the app,
    # app's may not have all the same attributes.
    json_data = models.CharField(
        blank=True,
        default='',
        max_length=2048,
        help_text=('JSON data for this app.'))

    # admin stuff
    date_hierarchy = 'publish_date'
    get_latest_by = 'publish_date'

    def __unicode__(self):
        """ returns string/unicode representation of project """
        s = self.name
        if self.version != "":
            s = s + " v. " + self.version
        return s

    def __str__(self):
        """ same as unicode() except str() """
        return str(self.__unicode__())

    def __repr__(self):
        """ same as unicode() """
        return self.__unicode__()

    def get_json(self):
        """ Reads the apps json_data and returns an object. """

        if self.json_data:
            try:
                jsonobj = json.loads(self.json_data)
            except Exception as ex:
                raise InvalidJsonData(ex)
            return jsonobj
        # No json_data.
        return None

    def set_json(self, obj, dosave=True):
        """ Sets json_data from an object.
            Returns True on success,
            raises InvalidJsonObject() on failure.
        """
        try:
            jsonstr = json.dumps(obj)
        except Exception as ex:
            raise InvalidJsonObject(ex)

        self.json_data = jsonstr
        if dosave:
            try:
                self.save()
            except Exception as ex:
                raise InvalidJsonObject(ex)
        return True

    # Meta info for the admin site
    class Meta:
        ordering = ['name']
        verbose_name = "App"
        verbose_name_plural = "Apps"


class InvalidJsonData(Exception):
    pass


class InvalidJsonObject(Exception):
    pass
