from django.db import models
import django.utils
import datetime

# Module level functions...   
def get_date_today():
    """ returns today's date for setting default publish_date value """
        
    return datetime.date.today()

# Create your models here.
class wp_project(models.Model):
    # project name
    name = models.CharField(blank=False, max_length=100)
    # alias for acessing projects by name
    # ...should be lowercase-no-spaces project name
    alias = models.CharField(blank=False, max_length=100)
    # short description of project 
    # (longer description should be in it's html file)
    description = models.CharField(blank=True, default="", max_length=1024)
    # version in the form of X.X.X or XX.X.X
    version = models.CharField(blank=True, default="1.0.0", max_length=6)
    # url to image file (will be embedded in html)
    logo_url = models.CharField(blank=True, default="", max_length=512)
    # html file for long description
    html_url = models.CharField(blank=True, default="", max_length=512)
    # url to package for download (/files/project-version.tar.gz)
    download_url = models.CharField(blank=True, default="", max_length=512)
    # directory for screenshot images
    screenshot_dir = models.CharField(blank=True, default="", max_length=512)
    # optional main source file (.py file to view)
    source_file = models.CharField(blank=True, default="", max_length=512)
    # optional source dir (dir containing source files to view)
    source_dir = models.CharField(blank=True, default="", max_length=512)
    # publish date (for sort-order mainly)
    publish_date = models.DateField(blank=False, default=get_date_today())
    
    # count of views/downloads
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    def __unicode__(self):
        """ returns string/unicode representation of project """
        s = self.name
        if self.version != "":
            s = s + " v. " + self.version
        return s


        

        
        
    
    
    