from django.contrib import admin
from .models import Issue


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'project', 'issue_type', 'severity',
        'priority', 'status', 'reporter', 'assignee', 'created_at'
    )
    list_filter = ('status', 'severity', 'priority', 'issue_type', 'project', 'created_at')
    search_fields = ('title', 'description', 'module', 'tags')
    list_editable = ('status', 'severity', 'priority', 'assignee')
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    raw_id_fields = ('reporter', 'assignee', 'project', 'duplicate_of')

    fieldsets = (
        ('Issue Details', {
            'fields': ('title', 'description', 'reproduction_steps', 'issue_type')
        }),
        ('Classification', {
            'fields': ('severity', 'priority', 'status', 'module', 'tags', 'environment')
        }),
        ('Assignment', {
            'fields': ('project', 'reporter', 'assignee')
        }),
        ('Duplicate Tracking', {
            'fields': ('is_duplicate', 'duplicate_of'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
