""" Welborn Productions - Home - Admin
    ...provides web admin for home app configuration.
"""
from django.contrib import admin
from solo.admin import SingletonModelAdmin
from home.models import home_config


class WpAdmin(SingletonModelAdmin):

    class Media:
        css = {
            'all': ('/css/wp-admin.min.css',)
        }


class WpAdminSite(admin.AdminSite):
    site_header = 'Welborn Productions Admin'
    site_title = 'Welborn Productions Administration'

admin_site = WpAdminSite()
admin_site.register(home_config, WpAdmin)
