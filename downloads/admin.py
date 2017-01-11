#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
    Welborn Productions - Downloads - Admin page
    Provides admin site for Downloads app (for things like file_tracker)

    -Christopher Welborn 5-25-2013
'''

from django.contrib import admin
from downloads.models import file_tracker
from home.admin import admin_site


class wp_downloadsAdmin(admin.ModelAdmin):
    # prepopulated_fields= {'alias': ('name'.replace(' ', '').lower(), )}
    pass


admin_site.register(file_tracker, wp_downloadsAdmin)
