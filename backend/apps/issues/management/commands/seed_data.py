"""
python manage.py seed_data            -> 5 users, 2 projects, 50 realistic bugs
python manage.py seed_data --flush    -> remove previously seeded data first

Seed accounts all use the password  BugFlow@2026
    admin1 (ADMIN)   manager1 (MANAGER)   dev1, dev2 (DEVELOPER)   qa1 (QA)

Safe to run more than once: without --flush it leaves existing seed data alone.
Output is deterministic (fixed random seed) so everyone on the team sees the same data.
(Week 2 - Nandhini)
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.collab.models import Project, ProjectMembership, ProjectMembershipRole
from apps.issues.models import Issue, IssuePriority, IssueSeverity, IssueStatus, IssueType

User = get_user_model()

PASSWORD = 'BugFlow@2026'

USERS = [
    # username, role, first, last, department
    ('admin1', 'ADMIN', 'Asha', 'Admin', 'Platform'),
    ('manager1', 'MANAGER', 'Meera', 'Manager', 'Engineering'),
    ('dev1', 'DEVELOPER', 'Dev', 'One', 'Backend'),
    ('dev2', 'DEVELOPER', 'Dev', 'Two', 'Frontend'),
    ('qa1', 'QA', 'Quinn', 'Tester', 'Quality'),
]

PROJECTS = [
    {
        'name': 'BugFlow Platform', 'key': 'BF',
        'description': 'The BugFlow issue tracking platform itself (dogfooding).',
        'members': {'manager1': 'LEAD', 'dev1': 'DEVELOPER', 'dev2': 'DEVELOPER', 'qa1': 'QA'},
    },
    {
        'name': 'Customer Support Portal', 'key': 'CSP',
        'description': 'Customer-facing support and ticketing portal.',
        'members': {'manager1': 'LEAD', 'dev1': 'DEVELOPER', 'dev2': 'DEVELOPER', 'qa1': 'QA'},
    },
]

# (title, module, severity, type, description)  - 25 per project
BF_ISSUES = [
    ('Login returns 500 when password contains a percent sign', 'Auth', 'CRITICAL', 'BUG', 'Server error on login for passwords containing % characters.'),
    ('JWT refresh token accepted after user is deactivated', 'Auth', 'HIGH', 'BUG', 'Deactivated users can keep refreshing tokens until the refresh token expires.'),
    ('Registration allows duplicate emails with different casing', 'Auth', 'MEDIUM', 'BUG', 'User@Example.com and user@example.com create two accounts.'),
    ('Add password reset via email link', 'Auth', 'LOW', 'FEATURE', 'Users cannot recover accounts without an admin.'),
    ('Dashboard summary cards show stale counts after closing an issue', 'Dashboard', 'MEDIUM', 'BUG', 'Counts update only after a full page refresh.'),
    ('Severity donut chart overlaps legend on small screens', 'Dashboard', 'LOW', 'BUG', 'Chart legend overlaps the donut below 768px width.'),
    ('Dashboard takes 6s to load with 10k issues', 'Dashboard', 'HIGH', 'BUG', 'Summary endpoint runs one query per severity.'),
    ('Kanban card loses assignee avatar after drag and drop', 'Kanban', 'MEDIUM', 'BUG', 'Avatar disappears until the board is reloaded.'),
    ('Cannot drag issue into Closed column on Firefox', 'Kanban', 'HIGH', 'BUG', 'Drop event never fires in Firefox 120.'),
    ('Allow WIP limits per Kanban column', 'Kanban', 'LOW', 'ENHANCEMENT', 'Teams want a warning when a column exceeds its limit.'),
    ('Notification bell count not cleared after Mark all as read', 'Notifications', 'MEDIUM', 'BUG', 'Badge still shows the old unread count.'),
    ('Duplicate email sent when issue is assigned twice quickly', 'Notifications', 'LOW', 'BUG', 'Two identical emails are queued for one assignment.'),
    ('Email notifications missing issue link', 'Notifications', 'MEDIUM', 'BUG', 'Notification text has no URL back to the issue.'),
    ('PDF report cuts off the last table column', 'Reports', 'MEDIUM', 'BUG', 'Fix rate column is clipped in A4 export.'),
    ('CSV export includes issues from projects the user cannot access', 'Reports', 'CRITICAL', 'BUG', 'Export ignores project membership filtering.'),
    ('Add sprint summary export', 'Reports', 'LOW', 'FEATURE', 'Managers want a one-page sprint summary PDF.'),
    ('GET /api/v1/bugs/ is slow when searching descriptions', 'API', 'HIGH', 'BUG', 'Search over description does a full table scan.'),
    ('PATCH issue with invalid status returns 500 instead of 400', 'API', 'HIGH', 'BUG', 'Unhandled exception for unknown status values.'),
    ('API error responses use inconsistent JSON shapes', 'API', 'MEDIUM', 'TECH_DEBT', 'Some errors return detail, others return field maps.'),
    ('Pagination links break when ordering by severity', 'API', 'MEDIUM', 'BUG', 'next URL drops the ordering parameter.'),
    ('Attachment upload accepts .exe files', 'Attachments', 'CRITICAL', 'BUG', 'No extension allow-list on uploads.'),
    ('Large screenshot upload times out at 10MB', 'Attachments', 'MEDIUM', 'BUG', 'Upload fails with 504 for files near the limit.'),
    ('Comment editor loses text on browser back navigation', 'Comments', 'LOW', 'BUG', 'Unsaved comment text is discarded.'),
    ('Mentions in comments do not notify the mentioned user', 'Comments', 'MEDIUM', 'FEATURE', 'Typing @dev1 has no effect on notifications.'),
    ('Upgrade Django to latest 5.x security release', 'Infrastructure', 'HIGH', 'TECH_DEBT', 'Pinned version is behind on security patches.'),
]

CSP_ISSUES = [
    ('Customer cannot log in with Google SSO on Safari', 'Login', 'HIGH', 'BUG', 'Redirect loop after Google consent screen in Safari 17.'),
    ('Session expires silently while filling a long ticket form', 'Login', 'MEDIUM', 'BUG', 'User loses typed content when the token expires.'),
    ('Account lockout message reveals whether the email exists', 'Login', 'MEDIUM', 'BUG', 'Different messages for unknown email and wrong password.'),
    ('New ticket form accepts empty subject', 'Tickets', 'MEDIUM', 'BUG', 'Client-side validation missing for the subject field.'),
    ('Ticket list shows wrong status badge colour for On Hold', 'Tickets', 'LOW', 'BUG', 'On Hold tickets render with the Closed colour.'),
    ('Agents see tickets from other departments', 'Tickets', 'CRITICAL', 'BUG', 'Department filter missing on the agent queue.'),
    ('Ticket SLA timer keeps running while waiting for customer', 'Tickets', 'HIGH', 'BUG', 'Timer should pause in Waiting on Customer state.'),
    ('Add canned responses for common questions', 'Tickets', 'LOW', 'FEATURE', 'Agents retype the same replies every day.'),
    ('Refund request charged twice on retry', 'Payments', 'CRITICAL', 'BUG', 'Retrying after a timeout creates a second refund.'),
    ('Invoice PDF shows wrong currency symbol for INR', 'Payments', 'MEDIUM', 'BUG', 'Rupee amounts are rendered with a dollar sign.'),
    ('Payment webhook retries flood the logs', 'Payments', 'LOW', 'TECH_DEBT', 'Every retry logs the full payload at INFO level.'),
    ('Search ignores accented characters', 'Search', 'MEDIUM', 'BUG', 'Searching resume does not find resume with accents.'),
    ('Search results page is empty for queries over 100 characters', 'Search', 'LOW', 'BUG', 'Long queries return no results and no error.'),
    ('Search suggestions are slow on first keystroke', 'Search', 'LOW', 'ENHANCEMENT', 'First suggestion request takes over 2s.'),
    ('Mobile menu does not close after selecting an item', 'Mobile UI', 'LOW', 'BUG', 'Menu stays open and covers the page on iOS.'),
    ('Ticket detail layout breaks on screens narrower than 360px', 'Mobile UI', 'MEDIUM', 'BUG', 'Horizontal scroll appears on small Android phones.'),
    ('Tap targets too small for the reply button', 'Mobile UI', 'LOW', 'ENHANCEMENT', 'Fails accessibility guidance for touch size.'),
    ('Reply emails land in spam for Outlook users', 'Email', 'HIGH', 'BUG', 'SPF alignment failing for the support sender domain.'),
    ('Email threading broken when subject is edited', 'Email', 'MEDIUM', 'BUG', 'Replies create new tickets instead of threading.'),
    ('Auto-reply sent for every message in a long thread', 'Email', 'MEDIUM', 'BUG', 'Auto-responder should fire once per new ticket.'),
    ('Support chat widget blocks the cookie banner', 'Chat', 'LOW', 'BUG', 'Widget overlaps the Accept button on load.'),
    ('Chat transcript missing last message when closed quickly', 'Chat', 'MEDIUM', 'BUG', 'Race condition between close and save.'),
    ('Admin audit log does not record role changes', 'Admin', 'HIGH', 'BUG', 'Role edits leave no audit entry.'),
    ('Bulk close tickets action times out above 500 tickets', 'Admin', 'MEDIUM', 'BUG', 'Request runs synchronously and hits the gateway timeout.'),
    ('Migrate legacy ticket data to the new schema', 'Admin', 'MEDIUM', 'TECH_DEBT', 'Old tickets still use the pre-2024 field layout.'),
]

# Status mix per 25 issues: mostly active work, some closed, a couple reopened
STATUS_PLAN = (
    [IssueStatus.OPEN] * 7 + [IssueStatus.TRIAGED] * 4 + [IssueStatus.IN_PROGRESS] * 5 +
    [IssueStatus.CODE_REVIEW] * 3 + [IssueStatus.QA_TESTING] * 3 + [IssueStatus.CLOSED] * 2 +
    [IssueStatus.REOPENED] * 1
)

PRIORITY_BY_SEVERITY = {
    'CRITICAL': [IssuePriority.URGENT],
    'HIGH': [IssuePriority.URGENT, IssuePriority.HIGH],
    'MEDIUM': [IssuePriority.HIGH, IssuePriority.MEDIUM],
    'LOW': [IssuePriority.MEDIUM, IssuePriority.LOW],
    'TRIVIAL': [IssuePriority.LOW],
}

ENVIRONMENTS = ['Production', 'Staging', 'Chrome 120 / Windows 11', 'Firefox 121 / Ubuntu', 'Safari 17 / macOS', 'Android 14 / Chrome']

STEPS = (
    "1. Sign in as a regular user.\n"
    "2. Open the {module} area.\n"
    "3. Perform the action described above.\n"
    "4. Observe the incorrect behaviour."
)


class Command(BaseCommand):
    help = "Seed 5 users, 2 projects and 50 realistic issues for development and QA."

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help="Delete previously seeded users, projects and issues first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        if Project.objects.filter(key__in=[p['key'] for p in PROJECTS]).exists():
            self.stdout.write(self.style.WARNING(
                "Seed data already present. Run with --flush to recreate it."))
            return

        rng = random.Random(42)
        users = self._create_users()
        total = 0
        for config, templates in zip(PROJECTS, (BF_ISSUES, CSP_ISSUES)):
            project = self._create_project(config, users)
            total += self._create_issues(project, templates, users, rng)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(users)} users, {len(PROJECTS)} projects and {total} issues. "
            f"Login with any seed username and password {PASSWORD}"))

    def _flush(self):
        keys = [p['key'] for p in PROJECTS]
        Issue.objects.filter(project__key__in=keys).delete()
        Project.objects.filter(key__in=keys).delete()
        User.objects.filter(username__in=[u[0] for u in USERS]).delete()
        self.stdout.write("Removed existing seed data.")

    def _create_users(self):
        users = {}
        for username, role, first, last, department in USERS:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@bugflow.test', 'role': role,
                    'first_name': first, 'last_name': last, 'department': department,
                    'is_staff': role == 'ADMIN',
                },
            )
            user.set_password(PASSWORD)
            user.save()
            users[username] = user
        return users

    def _create_project(self, config, users):
        project = Project.objects.create(
            name=config['name'], key=config['key'],
            description=config['description'], created_by=users['manager1'],
        )
        for username, role in config['members'].items():
            ProjectMembership.objects.create(project=project, user=users[username], role=ProjectMembershipRole(role))
        return project

    def _create_issues(self, project, templates, users, rng):
        statuses = STATUS_PLAN[:]
        rng.shuffle(statuses)
        developers = [users['dev1'], users['dev2']]
        reporters = [users['qa1'], users['qa1'], users['manager1']]
        now = timezone.now()
        created = []

        for index, (title, module, severity, issue_type, description) in enumerate(templates):
            status = statuses[index % len(statuses)]
            age_days = rng.randint(1, 45)
            created_at = now - timedelta(days=age_days, hours=rng.randint(0, 23))
            unassigned = status in (IssueStatus.OPEN, IssueStatus.TRIAGED) and rng.random() < 0.4

            issue = Issue.objects.create(
                title=title, description=description,
                reproduction_steps=STEPS.format(module=module),
                issue_type=IssueType(issue_type), severity=IssueSeverity(severity),
                priority=rng.choice(PRIORITY_BY_SEVERITY[severity]), status=status,
                module=module, tags=f"{module.lower()},{issue_type.lower()}",
                environment=rng.choice(ENVIRONMENTS), project=project,
                reporter=rng.choice(reporters),
                assignee=None if unassigned else rng.choice(developers),
                resolved_at=(created_at + timedelta(days=rng.randint(1, 5))) if status == IssueStatus.CLOSED else None,
            )
            # created_at is auto_now_add, so backdate it with an update
            Issue.objects.filter(pk=issue.pk).update(created_at=created_at, updated_at=created_at)
            created.append(issue)

        # Mark two issues per project as duplicates so merge/duplicate features have data
        for duplicate, master in ((created[5], created[4]), (created[11], created[10])):
            Issue.objects.filter(pk=duplicate.pk).update(is_duplicate=True, duplicate_of=master)

        return len(created)
