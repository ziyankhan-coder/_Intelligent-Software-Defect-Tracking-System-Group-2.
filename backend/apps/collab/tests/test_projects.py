"""
Milestone 1 QA - projects and project membership (test plan IDs: PRJ-xx, MEM-xx).
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.collab.models import Project, ProjectMembership

PROJECTS = '/api/v1/projects/'


def detail(pk):
    return f'{PROJECTS}{pk}/'


def members(pk, user_id=None):
    return f'{PROJECTS}{pk}/members/' + (f'{user_id}/' if user_id else '')


# -------------------------------------------------------------- create / read
class TestProjectCreate:
    def test_PRJ_01_manager_can_create_project_and_becomes_lead(self, auth, manager):
        response = auth(manager).post(PROJECTS, {'name': 'Gamma', 'key': 'GAM'}, format='json')
        assert response.status_code == 201
        project = Project.objects.get(key='GAM')
        assert project.created_by == manager
        assert project.memberships.get(user=manager).role == 'LEAD'

    def test_PRJ_02_admin_can_create_project(self, auth, admin):
        assert auth(admin).post(PROJECTS, {'name': 'Gamma', 'key': 'GAM'}, format='json').status_code == 201

    @pytest.mark.parametrize('role_fixture', ['dev', 'qa'])
    def test_PRJ_03_developer_and_qa_cannot_create_project(self, auth, request, role_fixture):
        user = request.getfixturevalue(role_fixture)
        assert auth(user).post(PROJECTS, {'name': 'Gamma', 'key': 'GAM'}, format='json').status_code == 403

    def test_PRJ_04_anonymous_cannot_create_project(self, client, db):
        assert client.post(PROJECTS, {'name': 'Gamma', 'key': 'GAM'}, format='json').status_code == 401

    def test_PRJ_05_key_is_normalised_to_uppercase(self, auth, manager):
        response = auth(manager).post(PROJECTS, {'name': 'Gamma', 'key': 'gam'}, format='json')
        assert response.status_code == 201 and response.json()['key'] == 'GAM'

    @pytest.mark.parametrize('bad_key', ['G', '1AB', 'TOO-LONG-KEY', 'A B', 'abcdefghijk'])
    def test_PRJ_06_invalid_keys_rejected(self, auth, manager, bad_key):
        assert auth(manager).post(PROJECTS, {'name': 'Gamma', 'key': bad_key}, format='json').status_code == 400

    def test_PRJ_07_duplicate_key_or_name_rejected(self, auth, manager, project):
        assert auth(manager).post(PROJECTS, {'name': 'Other', 'key': 'ALP'}, format='json').status_code == 400
        assert auth(manager).post(PROJECTS, {'name': 'Alpha', 'key': 'OTH'}, format='json').status_code == 400

    def test_PRJ_08_name_and_key_required(self, auth, manager):
        assert auth(manager).post(PROJECTS, {}, format='json').status_code == 400


class TestProjectVisibility:
    def test_PRJ_10_manager_sees_all_projects(self, auth, manager, project, other_project):
        keys = {p['key'] for p in auth(manager).get(PROJECTS).json()['results']}
        assert keys == {'ALP', 'BET'}

    def test_PRJ_11_developer_sees_only_own_projects(self, auth, dev, project, other_project):
        keys = {p['key'] for p in auth(dev).get(PROJECTS).json()['results']}
        assert keys == {'ALP'}

    def test_PRJ_12_user_without_projects_sees_empty_list(self, auth, dev2, project):
        # dev2 is a member of 'other_project' only, which is not created here
        assert auth(dev2).get(PROJECTS).json()['count'] == 0

    def test_PRJ_13_member_can_open_project_detail(self, auth, dev, project):
        response = auth(dev).get(detail(project.pk))
        assert response.status_code == 200 and response.json()['key'] == 'ALP'

    def test_PRJ_14_non_member_gets_404_for_project_detail(self, auth, dev, other_project):
        assert auth(dev).get(detail(other_project.pk)).status_code == 404

    def test_PRJ_15_manager_can_open_any_project(self, auth, manager, other_project):
        assert auth(manager).get(detail(other_project.pk)).status_code == 200

    def test_PRJ_16_counts_are_correct(self, auth, manager, project, make_issue):
        make_issue(project)
        make_issue(project)
        body = auth(manager).get(detail(project.pk)).json()
        assert body['members_count'] == 3 and body['issues_count'] == 2

    def test_PRJ_17_list_does_not_have_n_plus_one_queries(self, auth, manager, dev, make_issue):
        def add_projects(start, count):
            for i in range(start, start + count):
                p = Project.objects.create(name=f'P{i}', key=f'PK{i}', created_by=manager)
                ProjectMembership.objects.create(project=p, user=manager, role='LEAD')
                ProjectMembership.objects.create(project=p, user=dev, role='DEVELOPER')
                make_issue(p)

        client = auth(manager)
        add_projects(0, 2)
        with CaptureQueriesContext(connection) as small:
            client.get(PROJECTS)
        add_projects(2, 10)
        with CaptureQueriesContext(connection) as large:
            client.get(PROJECTS)
        assert len(large) <= len(small) + 1, f"{len(small)} queries for 2 projects vs {len(large)} for 12"


class TestProjectEditDelete:
    def test_PRJ_20_manager_can_update_project(self, auth, manager, project):
        response = auth(manager).patch(detail(project.pk), {'description': 'Updated'}, format='json')
        assert response.status_code == 200
        project.refresh_from_db()
        assert project.description == 'Updated'

    def test_PRJ_21_developer_cannot_update_project(self, auth, dev, project):
        assert auth(dev).patch(detail(project.pk), {'description': 'Hacked'}, format='json').status_code == 403

    def test_PRJ_22_qa_cannot_delete_project(self, auth, qa, project):
        assert auth(qa).delete(detail(project.pk)).status_code == 403
        assert Project.objects.filter(pk=project.pk).exists()

    def test_PRJ_23_manager_can_delete_project(self, auth, manager, project):
        assert auth(manager).delete(detail(project.pk)).status_code == 204
        assert not Project.objects.filter(pk=project.pk).exists()


# ----------------------------------------------------------------- membership
class TestMembership:
    def test_MEM_01_member_can_list_members(self, auth, dev, project):
        response = auth(dev).get(members(project.pk))
        assert response.status_code == 200
        assert {m['user']['username'] for m in response.json()} == {'manager', 'dev', 'qa'}

    def test_MEM_02_non_member_cannot_list_members(self, auth, dev, other_project):
        assert auth(dev).get(members(other_project.pk)).status_code == 404

    def test_MEM_03_manager_can_add_member(self, auth, manager, project, dev2):
        response = auth(manager).post(members(project.pk), {'user_id': dev2.pk, 'role': 'DEVELOPER'}, format='json')
        assert response.status_code == 201
        assert project.memberships.filter(user=dev2).exists()

    def test_MEM_04_added_member_gains_access(self, auth, manager, project, dev2):
        assert auth(dev2).get(detail(project.pk)).status_code == 404
        auth(manager).post(members(project.pk), {'user_id': dev2.pk}, format='json')
        assert auth(dev2).get(detail(project.pk)).status_code == 200

    def test_MEM_05_adding_existing_member_updates_role_without_duplicate(self, auth, manager, project, dev):
        response = auth(manager).post(members(project.pk), {'user_id': dev.pk, 'role': 'VIEWER'}, format='json')
        assert response.status_code == 200
        assert project.memberships.filter(user=dev).count() == 1
        assert project.memberships.get(user=dev).role == 'VIEWER'

    def test_MEM_06_unknown_user_rejected(self, auth, manager, project):
        assert auth(manager).post(members(project.pk), {'user_id': 99999}, format='json').status_code == 400

    def test_MEM_07_invalid_role_rejected(self, auth, manager, project, dev2):
        assert auth(manager).post(members(project.pk), {'user_id': dev2.pk, 'role': 'GOD'}, format='json').status_code == 400

    def test_MEM_08_missing_user_id_rejected(self, auth, manager, project):
        assert auth(manager).post(members(project.pk), {}, format='json').status_code == 400

    def test_MEM_09_unknown_project_404(self, auth, manager, dev2):
        assert auth(manager).post(members(99999), {'user_id': dev2.pk}, format='json').status_code == 404

    @pytest.mark.parametrize('role_fixture', ['dev', 'qa'])
    def test_MEM_10_developer_and_qa_cannot_add_members(self, auth, request, role_fixture, project, dev2):
        user = request.getfixturevalue(role_fixture)
        response = auth(user).post(members(project.pk), {'user_id': dev2.pk}, format='json')
        assert response.status_code == 403

    def test_MEM_11_manager_can_remove_member(self, auth, manager, project, dev):
        assert auth(manager).delete(members(project.pk, dev.pk)).status_code == 204
        assert not project.memberships.filter(user=dev).exists()

    def test_MEM_12_removed_member_loses_access(self, auth, manager, project, dev):
        auth(manager).delete(members(project.pk, dev.pk))
        assert auth(dev).get(detail(project.pk)).status_code == 404

    def test_MEM_13_removing_non_member_404(self, auth, manager, project, dev2):
        assert auth(manager).delete(members(project.pk, dev2.pk)).status_code == 404

    def test_MEM_14_developer_cannot_remove_members(self, auth, dev, project, qa):
        assert auth(dev).delete(members(project.pk, qa.pk)).status_code == 403
        assert project.memberships.filter(user=qa).exists()

    def test_MEM_15_cannot_remove_only_project_lead(self, auth, manager, project):
        response = auth(manager).delete(members(project.pk, manager.pk))
        assert response.status_code == 400
        assert project.memberships.filter(user=manager).exists()

    def test_MEM_16_can_remove_lead_when_another_lead_exists(self, auth, manager, project, dev):
        auth(manager).post(members(project.pk, None), {'user_id': dev.pk, 'role': 'LEAD'}, format='json')
        assert auth(manager).delete(members(project.pk, manager.pk)).status_code == 204

    def test_MEM_17_anonymous_cannot_touch_members(self, client, project, dev):
        assert client.get(members(project.pk)).status_code == 401
        assert client.post(members(project.pk), {'user_id': dev.pk}, format='json').status_code == 401
        assert client.delete(members(project.pk, dev.pk)).status_code == 401
