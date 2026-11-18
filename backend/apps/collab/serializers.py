from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMembership, ProjectMembershipRole
from apps.users.serializers import UserDetailSerializer

User = get_user_model()

class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ('id', 'project', 'user', 'user_id', 'role', 'role_display', 'joined_at')
        read_only_fields = ('id', 'project', 'joined_at')


class ProjectSerializer(serializers.ModelSerializer):
    created_by_detail = UserDetailSerializer(source='created_by', read_only=True)
    memberships = ProjectMembershipSerializer(many=True, read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    issues_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'key', 'description', 'created_by',
            'created_by_detail', 'memberships', 'members_count',
            'issues_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def get_issues_count(self, obj):
        # Gracefully handle before issues table is queried
        if hasattr(obj, 'issues'):
            return obj.issues.count()
        return 0

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        project = super().create(validated_data)
        # Automatically add creator as Project Lead
        ProjectMembership.objects.create(
            project=project,
            user=user,
            role=ProjectMembershipRole.LEAD
        )
        return project


class AssignMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(choices=ProjectMembershipRole.choices, default=ProjectMembershipRole.DEVELOPER)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User with this ID does not exist.")
        return value
