from django.db import models
from django.conf import settings

class Project(models.Model):
    """
    Project model grouping issues, sprints, and team members.
    """
    name = models.CharField(max_length=150, unique=True)
    key = models.CharField(max_length=10, unique=True, help_text="Short uppercase prefix, e.g. BF, SEC")
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMembership',
        related_name='assigned_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.key})"


class ProjectMembershipRole(models.TextChoices):
    LEAD = 'LEAD', 'Project Lead'
    DEVELOPER = 'DEVELOPER', 'Developer'
    QA = 'QA', 'QA Engineer'
    VIEWER = 'VIEWER', 'Observer'


class ProjectMembership(models.Model):
    """
    Project-User relationship tracking role inside the project.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(
        max_length=20,
        choices=ProjectMembershipRole.choices,
        default=ProjectMembershipRole.DEVELOPER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} -> {self.project.name} as {self.get_role_display()}"
