"""
Shared pytest fixtures for the BugFlow backend (QA - Nandhini).

Roles used throughout the tests:
    admin, manager  -> see every project, can create/edit projects
    dev, dev2       -> DEVELOPER, only see projects they belong to
    qa              -> QA tester, only sees projects they belong to
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.collab.models import Project, ProjectMembership, ProjectMembershipRole
from apps.issues.models import Issue

User = get_user_model()
PASSWORD = 'Str0ng!Pass#2026'


def make_user(username, role, **extra):
    return User.objects.create_user(
        username=username, email=f'{username}@bugflow.test',
        password=PASSWORD, role=role, **extra,
    )


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def admin(db):
    return make_user('admin', 'ADMIN')


@pytest.fixture
def manager(db):
    return make_user('manager', 'MANAGER')


@pytest.fixture
def dev(db):
    return make_user('dev', 'DEVELOPER')


@pytest.fixture
def dev2(db):
    return make_user('dev2', 'DEVELOPER')


@pytest.fixture
def qa(db):
    return make_user('qa', 'QA')


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth(db):
    """auth(user) -> an APIClient authenticated as that user."""
    def _auth(user):
        api = APIClient()
        api.force_authenticate(user=user)
        return api
    return _auth


@pytest.fixture
def project(db, manager, dev, qa):
    """Project 'Alpha' (key ALP) with manager as LEAD, dev as DEVELOPER and qa as QA."""
    project = Project.objects.create(name='Alpha', key='ALP', created_by=manager)
    ProjectMembership.objects.create(project=project, user=manager, role=ProjectMembershipRole.LEAD)
    ProjectMembership.objects.create(project=project, user=dev, role=ProjectMembershipRole.DEVELOPER)
    ProjectMembership.objects.create(project=project, user=qa, role=ProjectMembershipRole.QA)
    return project


@pytest.fixture
def other_project(db, manager, dev2):
    """A second project that dev and qa do NOT belong to."""
    project = Project.objects.create(name='Beta', key='BET', created_by=manager)
    ProjectMembership.objects.create(project=project, user=manager, role=ProjectMembershipRole.LEAD)
    ProjectMembership.objects.create(project=project, user=dev2, role=ProjectMembershipRole.DEVELOPER)
    return project


@pytest.fixture
def make_issue(db, qa):
    def _make(project, **overrides):
        data = {'title': 'Sample bug', 'project': project, 'reporter': qa}
        data.update(overrides)
        return Issue.objects.create(**data)
    return _make
