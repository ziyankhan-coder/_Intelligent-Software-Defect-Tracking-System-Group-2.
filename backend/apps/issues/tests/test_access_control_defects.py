"""
Milestone 1 QA - access control checks on issues (test plan IDs: SEC-xx).

Each test asserts the CORRECT (secure) behaviour. Tests that currently fail are
marked xfail(strict=False) and map to defect IDs in docs/qa/M1_QA_Report.md.
When a defect is fixed the test starts passing (XPASS) - delete the marker then.
"""

import pytest

BUGS = '/api/v1/bugs/'


@pytest.fixture
def foreign_issue(other_project, make_issue):
    """An issue in a project that `dev` and `qa` do not belong to."""
    return make_issue(other_project, title='Secret roadmap bug')


def test_SEC_01_non_member_cannot_read_issue_detail(auth, dev, foreign_issue):
    assert auth(dev).get(f'{BUGS}{foreign_issue.pk}/').status_code in (403, 404)


def test_SEC_02_non_member_cannot_edit_issue(auth, dev, foreign_issue):
    auth(dev).patch(f'{BUGS}{foreign_issue.pk}/', {'title': 'Defaced'}, format='json')
    foreign_issue.refresh_from_db()
    assert foreign_issue.title == 'Secret roadmap bug'


def test_SEC_03_summary_project_param_respects_membership(auth, dev, foreign_issue, other_project):
    body = auth(dev).get(f'{BUGS}summary/', {'project': other_project.pk}).json()
    assert body.get('total', 0) == 0


def test_SEC_04_resolved_at_cannot_be_set_by_client(auth, manager, project, make_issue):
    issue = make_issue(project)
    auth(manager).patch(f'{BUGS}{issue.pk}/', {'resolved_at': '2020-01-01T00:00:00Z'}, format='json')
    issue.refresh_from_db()
    assert issue.resolved_at is None


def test_SEC_05_assignee_must_be_project_member(auth, manager, project, dev2):
    response = auth(manager).post(
        BUGS, {'title': 'Bad assignee', 'project': project.pk, 'assignee': dev2.pk}, format='json')
    assert response.status_code == 400


def test_SEC_06_developer_cannot_close_issue(auth, dev, project, make_issue):
    issue = make_issue(project, status='QA_TESTING')
    response = auth(dev).patch(f'{BUGS}{issue.pk}/', {'status': 'CLOSED'}, format='json')
    assert response.status_code == 403


def test_SEC_07_reporter_is_always_the_logged_in_user(auth, qa, dev, project):
    """Reporter cannot be spoofed on creation."""
    response = auth(qa).post(BUGS, {'title': 'Spoof', 'project': project.pk, 'reporter': dev.pk}, format='json')
    assert response.status_code == 201 and response.json().get('id')
    from apps.issues.models import Issue
    assert Issue.objects.get(pk=response.json()['id']).reporter == qa


def test_SEC_08_qa_cannot_delete_issue(auth, qa, project, make_issue):
    issue = make_issue(project)
    assert auth(qa).delete(f'{BUGS}{issue.pk}/').status_code == 403
