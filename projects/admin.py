from django.contrib import admin
from projects.models import wp_project
from home.admin import admin_site


def enable_projects(modeladmin, request, queryset):
    """ enables projects (.disabled = False) """
    queryset.update(disabled=False)
enable_projects.short_description = "Enable selected Projects"


def disable_projects(modeladmin, request, queryset):
    """ disables projects (.disabled = True) """
    queryset.update(disabled=True)
disable_projects.short_description = "Disable selected Projects"


class wp_projectAdmin(admin.ModelAdmin):  # noqa
    prepopulated_fields = {
        'alias': ('name'.replace(' ', '').lower(),)
    }
    # enable actions above
    actions = [
        enable_projects,
        disable_projects]

admin_site.register(wp_project, wp_projectAdmin)
