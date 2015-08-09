""" Welborn Productions - Home - Admin
    ...provides web admin for home app configuration.
"""
from django.contrib import admin
from solo.admin import SingletonModelAdmin
from home.models import home_config


class WpAdminSite(admin.AdminSite):

    """ Global admin site. """
    site_header = 'Welborn Productions Admin'
    site_title = 'Welborn Productions Administration'

admin_site = WpAdminSite()
admin_site.register(home_config, SingletonModelAdmin)
