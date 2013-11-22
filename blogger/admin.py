#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: welbornproductions blog admin
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 19, 2013
'''

from django.contrib import admin
from blogger.models import wp_blog

# admin actions


def disable_posts(modeladmin, request, queryset):
    """ makes .disabled = True on all selected posts. """
    queryset.update(disabled=True)
disable_posts.short_description = "Disable selected Posts"


def enable_posts(modeladmin, request, queryset):
    """ makes .disabled = False on all selected posts. """
    queryset.update(disabled=False)
enable_posts.short_description = "Enable selected Posts"


def disable_comments(modeladmin, request, queryset):
    """ makes .enable_comments = False on selected posts."""
    queryset.update(enable_comments=False)
disable_comments.short_description = "Disable Comments in selected Posts"


def enable_comments(modeladmin, request, queryset):
    """ makes .enable_comments = True on selected posts."""
    queryset.update(enable_comments=True)
enable_comments.short_description = "Enable Comments in selected Posts"


class wp_blogAdmin(admin.ModelAdmin):
    #exclude = ['posted']
    prepopulated_fields = {'slug': ('title'.lower(),)
                           }
    # enable actions found above for this admin page.
    actions = [enable_posts,
               disable_posts,
               enable_comments,
               disable_comments]
    
admin.site.register(wp_blog, wp_blogAdmin)
