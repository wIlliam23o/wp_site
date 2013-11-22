#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Downloads - Admin page
     @summary: Provides admin site for Downloads app (for things like file_tracker)
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 25, 2013
'''

from django.contrib import admin
from downloads.models import file_tracker


class wp_downloadsAdmin(admin.ModelAdmin):
    # prepopulated_fields= {'alias': ('name'.replace(' ', '').lower(),)
    #                      }
    pass

    
admin.site.register(file_tracker, wp_downloadsAdmin)
