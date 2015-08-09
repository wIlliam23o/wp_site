from django.contrib import admin
from apps.models import wp_app
from home.admin import admin_site
# actions for admin page


def enable_apps(modeladmin, request, queryset):
    """ enables apps (.disabled = False) """
    queryset.update(disabled=False)
enable_apps.short_description = "Enable selected Apps"


def disable_apps(modeladmin, request, queryset):
    """ disables apps (.disabled = True) """
    queryset.update(disabled=True)
disable_apps.short_description = "Disable selected Apps"


class wp_appAdmin(admin.ModelAdmin):
    prepopulated_fields = {'alias': ('name'.replace(' ', '').lower(),)
                           }
    # enable actions above
    actions = [enable_apps,
               disable_apps]

admin_site.register(wp_app, wp_appAdmin)
