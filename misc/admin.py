'''
    Admin for welbornprod.misc

    Created on Oct 20, 2013

@author: Christopher Welborn
'''
from django.contrib import admin
from misc.models import wp_misc
from home.admin import admin_site

# actions for admin page


def enable_misc(modeladmin, request, queryset):
    """ enables misc (.disabled = False) """
    queryset.update(disabled=False)
enable_misc.short_description = "Enable selected Misc. objects"


def disable_misc(modeladmin, request, queryset):
    """ disables misc (.disabled = True) """
    queryset.update(disabled=True)
disable_misc.short_description = "Disable selected Misc. objects"


class wp_miscAdmin(admin.ModelAdmin):
    prepopulated_fields = {'alias': ('name'.replace(' ', '').lower(),)
                           }
    # enable actions above
    actions = [enable_misc,
               disable_misc]

admin_site.register(wp_misc, wp_miscAdmin)
