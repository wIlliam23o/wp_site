from django.db import models
from django.db.models import permalink

class wp_blog(models.Model):
    """ Welborn Productions Blog Object. """
    
    # content
    title = models.CharField(max_length=150, unique=True, blank=False)
    slug = models.SlugField(max_length=150, unique=True, blank=False)
    body = models.TextField(blank=True)
    html_url = models.CharField(max_length=200, blank=True)
    
    # tracking/sorting info.
    project = models.ManyToManyField('projects.wp_project', blank=True)
    posted = models.DateField(db_index=True, auto_now_add=True)
    tags = models.CharField(max_length=512, blank=False)
    
    
    def __unicode__(self):
        return '%s' % self.title
    
    @permalink
    def get_absolute_url(self):
        return ('view_post', None, { 'slug': self.slug })
