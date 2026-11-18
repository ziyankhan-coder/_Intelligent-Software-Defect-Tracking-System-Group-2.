from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Project, ProjectMembership, ProjectMembershipRole
from .serializers import ProjectSerializer, ProjectMembershipSerializer, AssignMemberSerializer
from apps.users.permissions import IsManagerOrAdmin

User = get_user_model()

class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/projects/ - List projects accessible to user
    POST /api/v1/projects/ - Create project (Managers and Admins)
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'MANAGER']:
            return Project.objects.all()
        # Non-managers see projects they are assigned to
        return Project.objects.filter(members=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsManagerOrAdmin()]
        return [permissions.IsAuthenticated()]


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/v1/projects/<id>/
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsManagerOrAdmin()]
        return [permissions.IsAuthenticated()]


class ProjectMemberAssignView(APIView):
    """
    POST /api/v1/projects/<pk>/members/ - Assign member to project
    DELETE /api/v1/projects/<pk>/members/<user_id>/ - Remove member
    """
    permission_classes = [IsManagerOrAdmin]

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
        membership.delete()
        return Response({"message": "Member removed from project successfully."}, status=status.HTTP_204_NO_CONTENT)
