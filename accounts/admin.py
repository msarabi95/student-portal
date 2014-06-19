# -*- coding: utf-8  -*-
from django import forms

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.contrib.auth import authenticate
from django.contrib.admin.sites import AdminSite
from userena.admin import UserenaAdmin

from clubs.models import Club


class DeanshipAuthenticationForm(admin.forms.AdminAuthenticationForm):
    """A custom authentication form used in the admin app.  Based on the
original Django code."""
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        message = admin.forms.ERROR_MESSAGE
        params = {'username': self.username_field.verbose_name}

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(message, code='invalid', params=params)
            # If the user isn't a deanship employee, they must not be
            # able to use the deanship admin interface.
            elif not self.user_cache.has_perm('deanship_employee'):
                raise forms.ValidationError(message, code='invalid', params=params)
        return self.cleaned_data

def remove_add_code_perm(modeladmin, request, queryset):
    add_code = Permission.objects.get(codename='add_code')
    for user in queryset:
        user.user_permissions.remove(add_code)
        user.save()
remove_add_code_perm.short_description = u"امنع من تسجيل نقاط"

def remove_add_book_perm(modeladmin, request, queryset):
    add_book = Permission.objects.get(codename='add_book')
    for user in queryset:
        user.user_permissions.remove(add_book)
        user.save()
remove_add_book_perm.short_description = u"امنع من إضافة الكتب"

def remove_add_bookrequest_perm(modeladmin, request, queryset):
    add_bookrequest = Permission.objects.get(codename='add_bookrequest')
    for user in queryset:
        user.user_permissions.remove(add_bookrequest)
        user.save()
remove_add_bookrequest_perm.short_description = u"امنع من طلب استعارة الكتب"

class DeanshipAdmin(AdminSite):
    """This admin website is for the Studnet Affairs Deanship employees
to modify user permissions (e.g. who is the coordinator of which
club)."""

    login_form = DeanshipAuthenticationForm

    def has_permission(self, request):
        """
        Removed check for is_staff.
        """
        return request.user.has_perm('')

class ModifiedUserAdmin(UserenaAdmin):
    """This changes the way the admin websites (both the main and deanship
ones) deal with the User model."""
    actions = [remove_add_code_perm, remove_add_bookrequest_perm,
               remove_add_book_perm]
    list_display = ('username', 'full_en_name', 'email', 'is_coordinator')

    def is_coordinator(self, obj):
        if obj.coordination.all():
            return True
        else:
            return False
    is_coordinator.boolean = True
    is_coordinator.short_description = u"منسق؟"

    def full_en_name(self, obj):
        fullname = ""
        try:
            # If the English first name is missing, let's assume the
            # rest is also missing.
            if obj.enjaz_profile.en_first_name:
                fullname = " ".join([obj.enjaz_profile.en_first_name,
                                     obj.enjaz_profile.en_middle_name,
                                     obj.enjaz_profile.en_last_name])
        except AttributeError: # If the user has their details missing
            pass

        # If no full name is provided, fallback to the username.
        if not fullname:
            fullname = obj.username

        return fullname
    full_en_name.short_description = u"الاسم الإنجليزي الكامل"

deanship_admin = DeanshipAdmin("Deanship Admin")
admin.site.unregister(User)
admin.site.register(User, ModifiedUserAdmin)
deanship_admin.register(User, ModifiedUserAdmin)
