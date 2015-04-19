from django.db import models
from django.db.models import permalink


class wp_blog(models.Model):

    """ Welborn Productions Blog Object. """

    # content
    title = models.CharField(max_length=150, unique=True, blank=False,
                             help_text="Title for the blog post (must be unique).")
    slug = models.SlugField(max_length=150, unique=True, blank=False,
                            help_text="Automatically generated slug for urls (can be overridden).")
    body = models.TextField(blank=True,
                            help_text="The body/message for this post. Can include HTML.")
    html_url = models.CharField(max_length=200, blank=True,
                                help_text="Optional external html file to override the .body.")
    enable_comments = models.BooleanField(default=True,
                                          help_text="If False, no comments will be loaded/shown for this post.")
    disabled = models.BooleanField(default=False,
                                   help_text="If True, this post will not be displayed. (as opposed to just deleting it)")

    # tracking/sorting info.
    project = models.ManyToManyField('projects.wp_project', blank=True,
                                     help_text="One or more wp_projects related to this post.")
    posted = models.DateField(db_index=True, auto_now_add=True,
                              help_text="The date this post was posted.")
    posted_time = models.TimeField(db_index=True, auto_now_add=True,
                                   help_text="The time this post was posted.")
    posted_datetime = models.DateTimeField(db_index=True, auto_now_add=True,
                                           help_text="Combination date and time this post was posted.")
    tags = models.CharField(max_length=512, blank=False,
                            help_text="Post tags, for filtering and searching posts by tag. (space-separated)")
    view_count = models.IntegerField(default=0, blank=False,
                                     help_text="How many times this post has been viewed.")

    # admin stuff
    date_hierarchy = 'posted_datetime'

    def __unicode__(self):
        """ returns title """

        return '%s' % self.title

    def __str__(self):
        """ same as unicode, but str() """
        return str(self.__unicode__())

    def __repr__(self):
        """ same as unicode """
        return self.__unicode__()

    @permalink
    def get_absolute_url(self):
        return ('view_post', None, {'slug': self.slug})

    def get_projects(self):
        return self.project.all()

    # Meta info for the admin site
    class Meta:
        get_latest_by = 'posted_datetime'
        ordering = ['-posted']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
