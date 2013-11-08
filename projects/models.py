from django.db import models
#import django.utils #@UnusedImport: utils
import datetime

# Module level functions...   
def get_date_today():
    """ returns today's date for setting default publish_date value """
        
    return datetime.date.today()

# Create your models here.
class wp_project(models.Model):
    # project name
    name = models.CharField(blank=False, max_length=100,
                            help_text="Name of the project. (Must be unique)")
    # alias for acessing projects by name
    # ...should be lowercase-no-spaces project name
    alias = models.CharField(blank=False, max_length=100,
                             help_text="Alias for this project (lowercase, used to build urls)")
    # short description of project 
    # (longer description should be in it's html file)
    description = models.CharField(blank=True, default="", max_length=1024,
                                   help_text="Short description for the project.")
    # version in the form of X.X.X or XX.X.X
    version = models.CharField(blank=True, default="1.0.0", max_length=6,
                               help_text="Version string in the form of X.X.X")
    # url to image file (will be embedded in html)
    logo_url = models.CharField(blank=True, default="", max_length=512,
                                help_text="URL of logo image (possible future development.)")
    # html file for long description
    html_url = models.CharField(blank=True, default="", max_length=512,
                                help_text="Html file for this project, containing the description.")
    # url to package for download (/files/project-version.tar.gz)
    download_url = models.CharField(blank=True, default="", max_length=512,
                                    help_text="Location of main file to download for the project. (Can be a directory)")
    # directory for screenshot images
    screenshot_dir = models.CharField(blank=True, default="", max_length=512,
                                      help_text="Directory containing screenshots for the project (Relative location)")
    # optional main source file (.py file to view)
    source_file = models.CharField(blank=True, default="", max_length=512,
                                   help_text="Main source code file for the project for viewing.")
    # optional source dir (dir containing source files to view)
    source_dir = models.CharField(blank=True, default="", max_length=512,
                                  help_text="Directory containing multiple source code files for viewing.")
    # publish date (for sort-order mainly)
    publish_date = models.DateField(blank=False, default=get_date_today(),
                                    help_text="Date the project was published. (Automatically set to today.)")
    
    # disables project (instead of deleting it, it simply won't be viewed)
    disabled = models.BooleanField(default=False)
    
    # count of views/downloads
    view_count = models.IntegerField(default=0,
                                     help_text="How many times this project has been viewed. (Integer)")
    download_count = models.IntegerField(default=0,
                                         help_text="How many times this project has been downloaded. (Integer)")
    
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
    
    # Meta info for the admin site
    class Meta:
        ordering = ['name']
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        
        

        
        
    
    
    