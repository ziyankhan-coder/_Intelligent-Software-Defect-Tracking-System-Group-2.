"""
Milestone 1 QA - Django admin panel (test plan IDs: ADM-xx).
Checks every registered model's list page loads, search works and filters render.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

ADMIN_MODELS = [
    ('users', 'customuser'),
    ('collab', 'project'),
    ('collab', 'projectmembership'),
    ('issues', 'issue'),
]


@pytest.fixture
def superuser_client(client, db):
    User.objects.create_superuser('root', 'root@bugflow.test', 'Str0ng!Pass#2026', role='ADMIN')
    client.login(username='root', password='Str0ng!Pass#2026')
    return client


@pytest.mark.parametrize('app,model', ADMIN_MODELS)
def test_ADM_01_changelist_loads(superuser_client, project, make_issue, app, model):
    make_issue(project, title='Admin visible')
    assert superuser_client.get(reverse(f'admin:{app}_{model}_changelist')).status_code == 200


@pytest.mark.parametrize('app,model,term', [
    ('users', 'customuser', 'dev'),
    ('collab', 'project', 'Alpha'),
    ('collab', 'projectmembership', 'dev'),
    ('issues', 'issue', 'Admin'),
])
def test_ADM_02_search_works(superuser_client, project, make_issue, app, model, term):
    make_issue(project, title='Admin visible')
    assert superuser_client.get(reverse(f'admin:{app}_{model}_changelist'), {'q': term}).status_code == 200


@pytest.mark.parametrize('app,model,params', [
    ('users', 'customuser', {'role': 'QA'}),
    ('collab', 'projectmembership', {'role': 'LEAD'}),
    ('issues', 'issue', {'status': 'OPEN', 'severity': 'HIGH'}),
])
def test_ADM_03_filters_work(superuser_client, project, make_issue, app, model, params):
    make_issue(project)
    assert superuser_client.get(reverse(f'admin:{app}_{model}_changelist'), params).status_code == 200


def test_ADM_04_project_page_shows_membership_inline(superuser_client, project):
    response = superuser_client.get(reverse('admin:collab_project_change', args=[project.pk]))
    assert response.status_code == 200 and b'memberships' in response.content


def test_ADM_05_non_staff_user_is_redirected_to_login(client, dev, password):
    client.login(username='dev', password=password)
    response = client.get(reverse('admin:index'))
    assert response.status_code == 302 and '/admin/login/' in response['Location']
