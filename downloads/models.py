from django.db import models
import os.path

# Create your models here.
class file_tracker(models.Model):
    """ holds info about a single file, to better track downloads """
    
    # Filename info.
    filename = models.CharField(max_length=1024, blank=False)
    shortname = models.CharField(max_length=512, default="", blank=True)
    location = models.CharField(max_length=1024, default="", blank=True)
    notes = models.TextField(default="", blank=True)
    # File is related to projects or blog posts?
    project = models.ManyToManyField('projects.wp_project', blank=True)
    post = models.ManyToManyField('blogger.wp_blog', blank=True)
    
    # General counts
    download_count = models.BigIntegerField(default=0)
    view_count = models.BigIntegerField(default=0)
    
    
    def __str__(self):
        return self.get_shortname(dosave=False)
    
    def __unicode__(self):
        return self.get_shortname(dosave=False)
    
    def get_shortname(self,dosave=False):
        """ retrieves shortname if it is set, 
            will set the shortname for you and return it
        """
        if self.filename is None:
            return None
        
        if (self.shortname is None) or (self.shortname == ""):
            self.shortname = os.path.split(self.filename)[1]
            if dosave: self.save()
        return self.shortname
    
    def get_location(self, dosave=False):
        """ retrieves dir for this file if it is set, 
            will set the location for you and return it
        """
        if self.filename is None:
            return None
        
        if (self.location is None) or (self.location == ""):
            self.location = os.path.split(self.filename)[0]
            if dosave: self.save()
        return self.location
    
    def set_filename(self, newfilename, updateinfo=True, dosave=True):
        """ sets the filename and saves it 
            (just like myfile.filename=blah, myfile.save())
        """
        
        if newfilename is None:
            return None
        self.filename = newfilename
        if updateinfo:
            self.get_location()
            self.get_shortname()
        if dosave: self.save()
        return self.filename
    
    
    # Meta info for the admin site
    class Meta:
        ordering = ['shortname']
        verbose_name = "File Tracker"
        verbose_name_plural = "File Trackers"
        
    