from django.contrib import admin, messages
from img.models import wp_image


def disable_sel(modeladmin, request, queryset):
    """ disables images (.disabled = True) """
    dcnt = queryset.update(disabled=True)
    pstr = plural(dcnt, 'image')
    msg = 'Disabled {} {}.'.format(dcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
disable_sel.short_description = 'Disable selected images'


def enable_sel(modeladmin, request, queryset):
    """ enables images (.disabled = False) """
    encnt = queryset.update(disabled=False)
    pstr = plural(encnt, 'image')
    msg = 'Enabled {} {}.'.format(encnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
enable_sel.short_description = 'Enable selected images'


def plural(cnt, word, pluralform=None):
    """ Pluralize a word based on a count. """
    if cnt == 1:
        return word
    if pluralform is not None:
        return pluralform
    return '{}s'.format(word)


def privatize_sel(modeladmin, request, queryset):
    """ marks selected images as private. """
    selcnt = len(queryset)
    privcnt = queryset.update(private=True)
    pstr = plural(selcnt, 'image was', 'images were')
    msg = '{} of {} {} marked as private.'.format(privcnt, selcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return privcnt
privatize_sel.short_description = 'Privatize selected images'


def unprivatize_sel(modeladmin, request, queryset):
    """ marks selected images as private. """
    selcnt = len(queryset)
    privcnt = queryset.update(private=False)
    pstr = plural(selcnt, 'image was', 'images were')
    msg = '{} of {} {} marked as not private.'.format(privcnt, selcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return privcnt
unprivatize_sel.short_description = 'Unprivatize selected images'


class wp_imageAdmin(admin.ModelAdmin):  # noqa
    actions = [
        disable_sel,
        enable_sel,
        privatize_sel,
        unprivatize_sel
    ]


admin.site.register(wp_image, wp_imageAdmin)
