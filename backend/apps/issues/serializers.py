"""
Issue Serializers - Week 1
Handles validation and serialization for Issue CRUD operations.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Issue, IssueStatus, IssueSeverity, IssuePriority, IssueType
from apps.users.serializers import UserDetailSerializer

User = get_user_model()


class IssueListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for issue list views.
    """
    reporter_detail = UserDetailSerializer(source='reporter', read_only=True)
    assignee_detail = UserDetailSerializer(source='assignee', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_key = serializers.CharField(source='project.key', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_issue_type_display', read_only=True)

    class Meta:
        model = Issue
        fields = (
            'id', 'title', 'issue_type', 'type_display',
            'severity', 'severity_display', 'priority', 'priority_display',
            'status', 'status_display', 'module', 'tags',
            'project', 'project_name', 'project_key',
            'reporter', 'reporter_detail', 'assignee', 'assignee_detail',
            'is_duplicate', 'created_at', 'updated_at'
        )


class IssueDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for single-issue detail views.
    """
    reporter_detail = UserDetailSerializer(source='reporter', read_only=True)
    assignee_detail = UserDetailSerializer(source='assignee', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_key = serializers.CharField(source='project.key', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_issue_type_display', read_only=True)
    duplicate_of_title = serializers.CharField(source='duplicate_of.title', read_only=True, default=None)

    class Meta:
        model = Issue
        fields = (
            'id', 'title', 'description', 'reproduction_steps',
            'issue_type', 'type_display',
            'severity', 'severity_display', 'priority', 'priority_display',
            'status', 'status_display',
            'module', 'tags', 'environment',
            'project', 'project_name', 'project_key',
            'reporter', 'reporter_detail', 'assignee', 'assignee_detail',
            'is_duplicate', 'duplicate_of', 'duplicate_of_title',
            'created_at', 'updated_at', 'resolved_at'
        )
        read_only_fields = ('id', 'reporter', 'created_at', 'updated_at', 'resolved_at')


class IssueCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new issue.
    Reporter is automatically set to the authenticated user.
    """
    class Meta:
        model = Issue
        fields = (
            'id', 'title', 'description', 'reproduction_steps',
            'issue_type', 'severity', 'priority',
            'module', 'tags', 'environment',
            'project', 'assignee'
        )

    def validate_project(self, value):
        """Ensure the user has access to the project."""
        user = self.context['request'].user
        if user.is_staff or user.role in ['ADMIN', 'MANAGER']:
            return value
        if not value.members.filter(id=user.id).exists():
            raise serializers.ValidationError("You are not a member of this project.")
        return value

    def validate(self, attrs):
        project = attrs.get('project')
        assignee = attrs.get('assignee')
        # D-07: Assignee must be a member of the project
        if project and assignee:
            if not project.members.filter(id=assignee.id).exists():
                raise serializers.ValidationError({"assignee": "Assignee must be a member of the project."})
        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class IssueUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing issue.
    Status transitions will be validated by the state machine in Week 3.
    """
    class Meta:
        model = Issue
        fields = (
            'title', 'description', 'reproduction_steps',
            'issue_type', 'severity', 'priority', 'status',
            'module', 'tags', 'environment',
            'assignee', 'is_duplicate', 'duplicate_of'
        )

    def validate(self, attrs):
        assignee = attrs.get('assignee')
        # D-07: Assignee must be a member of the project
        if assignee and self.instance and self.instance.project:
            if not self.instance.project.members.filter(id=assignee.id).exists():
                raise serializers.ValidationError({"assignee": "Assignee must be a member of the project."})
        return attrs

    def validate_status(self, value):
        """
        Basic status transition validation.
        Full state machine (Open → Triaged → In Progress → Code Review → QA Testing → Closed)
        will be enforced in Week 3 by Ziyan.
        """
        if self.instance and value == IssueStatus.CLOSED and self.instance.status == IssueStatus.OPEN:
            raise serializers.ValidationError(
                "Cannot close an issue directly from Open status. "
                "It must go through the workflow stages."
            )
        return value
