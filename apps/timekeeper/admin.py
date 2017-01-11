""" Welborn Productions - Apps - TimeKeeper - Admin
    Provides django admin for the timekeeper app.
    -Christopher Welborn 1-11-16
"""
from home.admin import admin_site
from apps.timekeeper.models import (
    TKConfig,
    TKAddress,
    TKEmployee,
    TKJob,
    TKSession,
    TKZipCode,
)

from django.contrib import admin
from solo.admin import SingletonModelAdmin


class TKAddressAdmin(admin.ModelAdmin):
    pass


class TKEmployeeAdmin(admin.ModelAdmin):
    pass


class TKJobAdmin(admin.ModelAdmin):
    pass


class TKSessionAdmin(admin.ModelAdmin):
    pass


class TKZipCodeAdmin(admin.ModelAdmin):
    pass


admin_site.register(TKConfig, SingletonModelAdmin)
admin_site.register(TKAddress, TKAddressAdmin)
admin_site.register(TKEmployee, TKEmployeeAdmin)
admin_site.register(TKJob, TKJobAdmin)
admin_site.register(TKSession, TKSessionAdmin)
admin_site.register(TKZipCode, TKZipCodeAdmin)
