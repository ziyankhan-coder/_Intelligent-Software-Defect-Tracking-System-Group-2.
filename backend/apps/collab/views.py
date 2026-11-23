from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Project, ProjectMembership, ProjectMembershipRole
from .serializers import ProjectSerializer, ProjectMembershipSerializer, AssignMemberSerializer
from apps.users.permissions import IsManagerOrAdmin

User = get_user_model()


def _sees_all_projects(user):
    """Admins, Managers and Django staff can see every project."""
    return user.is_staff or getattr(user, 'role', '') in ('ADMIN', 'MANAGER')


def _visible_projects(user):
    """
    Projects the user may see, with related rows pre-loaded so the list
    endpoint does not issue extra queries per project (N+1).
    """
    queryset = (
        Project.objects
        .select_related('created_by')
        .prefetch_related('memberships__user')
        .annotate(_issues_count=Count('issues', distinct=True))
        # annotate() drops the model's default ordering, so set it explicitly
        .order_by('-created_at', '-id')
    )
    if _sees_all_projects(user):
        return queryset
    # Non-managers only see projects they are assigned to
    return queryset.filter(memberships__user=user)


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/projects/ - List projects accessible to user
    POST /api/v1/projects/ - Create project (Managers and Admins)
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _visible_projects(self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsManagerOrAdmin()]
        return [permissions.IsAuthenticated()]


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/v1/projects/<id>/
    Reading is limited to project members (and Managers/Admins).
    Non-members get a 404 so project existence is not leaked.
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _visible_projects(self.request.user)

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsManagerOrAdmin()]
        return [permissions.IsAuthenticated()]


class ProjectMemberAssignView(APIView):
    """
    GET    /api/v1/projects/<pk>/members/            - List project members
    POST   /api/v1/projects/<pk>/members/            - Assign / update member role
    DELETE /api/v1/projects/<pk>/members/<user_id>/  - Remove member
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAdmin()]

    def get(self, request, pk):
        # _visible_projects hides projects the user does not belong to
        project = get_object_or_404(_visible_projects(request.user), pk=pk)
        memberships = project.memberships.select_related('user').order_by('user__username')
        return Response(ProjectMembershipSerializer(memberships, many=True).data)

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = AssignMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data['role']
        user = get_object_or_404(User, id=user_id)

        membership, created = ProjectMembership.objects.update_or_create(
            project=project,
            user=user,
            defaults={'role': role}
        )

        return Response(
            ProjectMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def delete(self, request, pk, user_id=None):
        project = get_object_or_404(Project, pk=pk)
        membership = get_object_or_404(ProjectMembership, project=project, user_id=user_id)

        # A project must always keep at least one lead
        if membership.role == ProjectMembershipRole.LEAD:
            other_leads = project.memberships.filter(role=ProjectMembershipRole.LEAD).exclude(pk=membership.pk)
            if not other_leads.exists():
                return Response(
                    {"detail": "Cannot remove the only Project Lead. Assign another lead first."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        membership.delete()
        return Response({"message": "Member removed from project successfully."}, status=status.HTTP_204_NO_CONTENT)
