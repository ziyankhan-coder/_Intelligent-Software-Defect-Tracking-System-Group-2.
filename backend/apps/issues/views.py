"""
Issue Views - Week 1
API endpoints for Issue CRUD operations.
"""

from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .listing import (
    IssueExtraFilterBackend,
    IssueOrderingFilter,
    IssuePagination,
    IssueSearchFilter,
)
from .models import Issue, IssueStatus
from .serializers import (
    IssueListSerializer,
    IssueDetailSerializer,
    IssueCreateSerializer,
    IssueUpdateSerializer,
)


class IssueListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/bugs/     — List issues (with search & filters)
    POST /api/v1/bugs/     — Create a new issue
    """
    permission_classes = [permissions.IsAuthenticated]
    # Pagination / sorting / search live in listing.py (Nandhini, Week 2)
    pagination_class = IssuePagination
    filter_backends = [IssueExtraFilterBackend, IssueSearchFilter, IssueOrderingFilter]
    search_fields = [
        'title', 'description', 'module', 'tags',
        'reporter__username', 'assignee__username',
        'project__name', 'project__key',
    ]
    ordering_fields = ['id', 'title', 'created_at', 'updated_at', 'severity', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IssueCreateSerializer
        return IssueListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Issue.objects.select_related(
            'project', 'reporter', 'assignee'
        )

        # Admins & Managers see all; others see issues from their projects
        if not (user.is_staff or user.role in ['ADMIN', 'MANAGER']):
            queryset = queryset.filter(project__members=user)

        # Query parameter filters
        project_id = self.request.query_params.get('project')
        issue_status = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        priority = self.request.query_params.get('priority')
        issue_type = self.request.query_params.get('type')
        assignee_id = self.request.query_params.get('assignee')
        reporter_id = self.request.query_params.get('reporter')

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if issue_status:
            queryset = queryset.filter(status=issue_status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if priority:
            queryset = queryset.filter(priority=priority)
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        if reporter_id:
            queryset = queryset.filter(reporter_id=reporter_id)

        return queryset


class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/bugs/<id>/  — Retrieve issue details
    PATCH  /api/v1/bugs/<id>/  — Update issue fields
    DELETE /api/v1/bugs/<id>/  — Delete an issue (Managers/Admins only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Issue.objects.select_related('project', 'reporter', 'assignee', 'duplicate_of')
        # D-03: Restrict issue details to projects the user is a member of
        if not (user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'MANAGER']):
            queryset = queryset.filter(project__members=user)
        return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return IssueUpdateSerializer
        return IssueDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # D-08: Developers cannot close issues; QA/Manager/Admin only
        new_status = request.data.get('status')
        if new_status == IssueStatus.CLOSED:
            user = request.user
            if getattr(user, 'role', '') == 'DEVELOPER' and not user.is_staff:
                return Response(
                    {"detail": "Developers cannot close issues. Only QA Testers, Managers, or Admins can close issues."},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Auto-set resolved_at when status changes to CLOSED
        if instance.status == IssueStatus.CLOSED and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            instance.save(update_fields=['resolved_at'])
        # Clear resolved_at when reopened
        elif instance.status == IssueStatus.REOPENED and instance.resolved_at:
            instance.resolved_at = None
            instance.save(update_fields=['resolved_at'])

    def destroy(self, request, *args, **kwargs):
        """Only Managers and Admins can delete issues."""
        if not (request.user.is_staff or request.user.role in ['ADMIN', 'MANAGER']):
            return Response(
                {"detail": "Only Managers and Admins can delete issues."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class IssueSummaryView(APIView):
    """
    GET /api/v1/bugs/summary/
    Returns aggregated bug counts for the Dashboard.
    Used by Ramya's frontend Dashboard Summary Cards.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = Issue.objects.all()

        # D-04: Filter by user membership first so foreign project counts don't leak
        if not (user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'MANAGER']):
            queryset = queryset.filter(project__members=user)

        # Filter by project if specified
        project_id = request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        total = queryset.count()
        open_count = queryset.filter(status=IssueStatus.OPEN).count()
        in_progress = queryset.filter(status=IssueStatus.IN_PROGRESS).count()
        critical = queryset.filter(severity='CRITICAL').count()
        resolved = queryset.filter(status=IssueStatus.CLOSED).count()
        reopened = queryset.filter(status=IssueStatus.REOPENED).count()

        return Response({
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'critical': critical,
            'resolved': resolved,
            'reopened': reopened,
            'by_severity': {
                'critical': critical,
                'high': queryset.filter(severity='HIGH').count(),
                'medium': queryset.filter(severity='MEDIUM').count(),
                'low': queryset.filter(severity='LOW').count(),
                'trivial': queryset.filter(severity='TRIVIAL').count(),
            },
            'by_status': {
                'open': open_count,
                'triaged': queryset.filter(status=IssueStatus.TRIAGED).count(),
                'in_progress': in_progress,
                'code_review': queryset.filter(status=IssueStatus.CODE_REVIEW).count(),
                'qa_testing': queryset.filter(status=IssueStatus.QA_TESTING).count(),
                'closed': resolved,
                'reopened': reopened,
            }
        })
