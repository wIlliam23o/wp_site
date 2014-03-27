from django.contrib import admin
from apps.phonewords.models import pw_result
# actions for admin page


def enable_results(modeladmin, request, queryset):
    """ enables results (.disabled = False) """
    queryset.update(disabled=False)
enable_results.short_description = "Enable selected Results"


def disable_results(modeladmin, request, queryset):
    """ disables results (.disabled = True) """
    queryset.update(disabled=True)
disable_results.short_description = "Disable selected Results"


class pw_resultAdmin(admin.ModelAdmin):
    # enable actions above
    actions = [enable_results,
               disable_results]
    
admin.site.register(pw_result, pw_resultAdmin)
