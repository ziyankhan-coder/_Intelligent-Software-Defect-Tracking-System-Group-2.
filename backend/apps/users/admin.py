from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('BugFlow Role & Organization', {
            'fields': ('role', 'department')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('BugFlow Role & Organization', {
            'fields': ('role', 'department', 'email')
        }),
    )
