from django.contrib import admin
from projects.models import wp_project


class wp_projectAdmin(admin.ModelAdmin):
    prepopulated_fields= {'alias': ('name'.replace(' ', '').lower(),)
                          }
    
admin.site.register(wp_project, wp_projectAdmin)
