"""
BugFlow Issue Model - Core Issue Tracking
Designed by Ziyan (Backend Lead) - Week 1

Implements the central Issue/Bug model with:
- Severity & Priority classification
- Workflow status tracking (state machine transitions enforced in Week 3)
- Project & User relationships
- Environment and reproduction details
"""

from django.db import models
from django.conf import settings


class IssueSeverity(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Critical'
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'
    TRIVIAL = 'TRIVIAL', 'Trivial'


class IssuePriority(models.TextChoices):
    URGENT = 'URGENT', 'Urgent'
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'


class IssueStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    TRIAGED = 'TRIAGED', 'Triaged'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    CODE_REVIEW = 'CODE_REVIEW', 'Code Review'
    QA_TESTING = 'QA_TESTING', 'QA Testing'
    CLOSED = 'CLOSED', 'Closed'
    REOPENED = 'REOPENED', 'Reopened'


class IssueType(models.TextChoices):
    BUG = 'BUG', 'Bug'
    FEATURE = 'FEATURE', 'Feature Request'
    ENHANCEMENT = 'ENHANCEMENT', 'Enhancement'
    TASK = 'TASK', 'Task'
    SUPPORT = 'SUPPORT', 'Support Ticket'
    TECH_DEBT = 'TECH_DEBT', 'Technical Debt'


class Issue(models.Model):
    """
    Central Issue model for the BugFlow platform.
    Tracks bugs, features, enhancements, and tasks across projects.
    """

    # Core fields
    title = models.CharField(max_length=300, help_text="Short descriptive title for the issue.")
    description = models.TextField(blank=True, default='', help_text="Detailed description of the issue.")
    reproduction_steps = models.TextField(
        blank=True, default='',
        help_text="Step-by-step instructions to reproduce the bug."
    )

    # Classification
    issue_type = models.CharField(
        max_length=20,
        choices=IssueType.choices,
        default=IssueType.BUG,
        help_text="Type of issue: Bug, Feature, Enhancement, etc."
    )
    severity = models.CharField(
        max_length=20,
        choices=IssueSeverity.choices,
        default=IssueSeverity.MEDIUM,
        help_text="How severe the impact of this issue is."
    )
    priority = models.CharField(
        max_length=20,
        choices=IssuePriority.choices,
        default=IssuePriority.MEDIUM,
        help_text="How urgently this issue needs to be resolved."
    )
    status = models.CharField(
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.OPEN,
        help_text="Current workflow status of the issue."
    )

    # Categorization & context
    module = models.CharField(
        max_length=100,
        blank=True, default='',
        help_text="Affected software module or component (e.g., 'Auth', 'Dashboard', 'API')."
    )
    tags = models.CharField(
        max_length=500,
        blank=True, default='',
        help_text="Comma-separated tags for filtering and categorization."
    )
    environment = models.CharField(
        max_length=200,
        blank=True, default='',
        help_text="Environment details (e.g., 'Production', 'Staging', 'Chrome 120, Windows 11')."
    )

    # Relationships
    project = models.ForeignKey(
        'collab.Project',
        on_delete=models.CASCADE,
        related_name='issues',
        help_text="Project this issue belongs to."
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_issues',
        help_text="User who reported this issue."
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues',
        help_text="Developer currently assigned to resolve this issue."
    )

    # Duplicate tracking (for Nandhini's merge feature in Week 3)
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates',
        help_text="If this is a duplicate, link to the master issue."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['severity']),
            models.Index(fields=['priority']),
            models.Index(fields=['assignee']),
            models.Index(fields=['reporter']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Issue'
        verbose_name_plural = 'Issues'

    def __str__(self):
        return f"[{self.project.key if self.project else 'N/A'}-{self.id}] {self.title}"

    @property
    def is_resolved(self):
        return self.status == IssueStatus.CLOSED

    @property
    def tag_list(self):
        """Return tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
