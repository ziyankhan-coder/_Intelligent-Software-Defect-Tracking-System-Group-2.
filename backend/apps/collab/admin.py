from django.contrib import admin
from .models import Project, ProjectMembership

class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    autocomplete_fields = ('user',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'created_by', 'get_members_count', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('name', 'key', 'description')
    inlines = [ProjectMembershipInline]

    def get_members_count(self, obj):
        return obj.members.count()
    get_members_count.short_description = 'Members'

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    list_filter = ('role', 'joined_at', 'project')
    search_fields = ('project__name', 'user__username', 'user__email')
