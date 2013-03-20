#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welbornproductions blog admin
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 19, 2013
'''

from django.contrib import admin
from blogger.models import wp_blog

class wp_blogAdmin(admin.ModelAdmin):
    #exclude = ['posted']
    prepopulated_fields = {'slug': ('title'.lower(),)
                           }
    
admin.site.register(wp_blog, wp_blogAdmin)


