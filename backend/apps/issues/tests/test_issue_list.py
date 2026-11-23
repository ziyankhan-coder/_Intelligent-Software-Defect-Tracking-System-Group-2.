"""
Milestone 1 QA - issue creation, list, pagination, sorting, search and filters
(test plan IDs: ISS-xx, LST-xx).
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.issues.models import Issue

BUGS = '/api/v1/bugs/'


def results(response):
    return response.json()['results']


def titles(response):
    return [r['title'] for r in results(response)]


# ------------------------------------------------------------------- creation
class TestIssueCreate:
    def payload(self, project, **overrides):
        data = {'title': 'Crash on save', 'project': project.pk, 'severity': 'HIGH'}
        data.update(overrides)
        return data

    def test_ISS_01_member_can_create_issue_and_is_reporter(self, auth, qa, project):
        response = auth(qa).post(BUGS, self.payload(project), format='json')
        assert response.status_code == 201
        issue = Issue.objects.get(pk=response.json()['id'])
        assert issue.reporter == qa and issue.status == 'OPEN'

    def test_ISS_02_defaults_applied(self, auth, qa, project):
        issue = Issue.objects.get(pk=auth(qa).post(BUGS, {'title': 'Defaults', 'project': project.pk}, format='json').json()['id'])
        assert (issue.severity, issue.priority, issue.issue_type) == ('MEDIUM', 'MEDIUM', 'BUG')

    def test_ISS_03_non_member_cannot_create_in_project(self, auth, dev, other_project):
        assert auth(dev).post(BUGS, self.payload(other_project), format='json').status_code == 400

    def test_ISS_04_manager_can_create_in_any_project(self, auth, manager, other_project):
        assert auth(manager).post(BUGS, self.payload(other_project), format='json').status_code == 201

    @pytest.mark.parametrize('field,value', [
        ('severity', 'EXTREME'), ('priority', 'ASAP'), ('issue_type', 'RANT'), ('title', ''),
    ])
    def test_ISS_05_invalid_values_rejected(self, auth, qa, project, field, value):
        assert auth(qa).post(BUGS, self.payload(project, **{field: value}), format='json').status_code == 400

    def test_ISS_06_title_and_project_required(self, auth, qa, project):
        assert auth(qa).post(BUGS, {'project': project.pk}, format='json').status_code == 400
        assert auth(qa).post(BUGS, {'title': 'No project'}, format='json').status_code == 400

    def test_ISS_07_anonymous_cannot_create(self, client, project):
        assert client.post(BUGS, self.payload(project), format='json').status_code == 401

    def test_ISS_08_cannot_close_directly_from_open(self, auth, manager, project, make_issue):
        issue = make_issue(project)
        response = auth(manager).patch(f'{BUGS}{issue.pk}/', {'status': 'CLOSED'}, format='json')
        assert response.status_code == 400

    def test_ISS_09_closing_sets_resolved_at_and_reopen_clears_it(self, auth, manager, project, make_issue):
        issue = make_issue(project, status='QA_TESTING')
        client = auth(manager)
        client.patch(f'{BUGS}{issue.pk}/', {'status': 'CLOSED'}, format='json')
        issue.refresh_from_db()
        assert issue.resolved_at is not None
        client.patch(f'{BUGS}{issue.pk}/', {'status': 'REOPENED'}, format='json')
        issue.refresh_from_db()
        assert issue.resolved_at is None

    def test_ISS_10_only_manager_or_admin_can_delete(self, auth, dev, manager, project, make_issue):
        issue = make_issue(project)
        assert auth(dev).delete(f'{BUGS}{issue.pk}/').status_code == 403
        assert auth(manager).delete(f'{BUGS}{issue.pk}/').status_code == 204


# ----------------------------------------------------------------- visibility
class TestIssueVisibility:
    def test_ISS_20_developer_sees_only_member_project_issues(self, auth, dev, project, other_project, make_issue):
        make_issue(project, title='Mine')
        make_issue(other_project, title='Not mine')
        assert titles(auth(dev).get(BUGS)) == ['Mine']

    def test_ISS_21_manager_sees_all_issues(self, auth, manager, project, other_project, make_issue):
        make_issue(project)
        make_issue(other_project)
        assert auth(manager).get(BUGS).json()['count'] == 2

    def test_ISS_22_project_filter_cannot_bypass_visibility(self, auth, dev, other_project, make_issue):
        make_issue(other_project)
        assert auth(dev).get(BUGS, {'project': other_project.pk}).json()['count'] == 0

    def test_ISS_23_list_requires_login(self, client, db):
        assert client.get(BUGS).status_code == 401


# ----------------------------------------------------------------- pagination
class TestPagination:
    @pytest.fixture
    def many(self, project, make_issue):
        for i in range(25):
            make_issue(project, title=f'Bug {i:02d}')

    def test_LST_01_default_page_size_is_10(self, auth, manager, many):
        body = auth(manager).get(BUGS).json()
        assert body['count'] == 25 and len(body['results']) == 10 and body['next'] and body['previous'] is None

    def test_LST_02_page_size_parameter(self, auth, manager, many):
        assert len(results(auth(manager).get(BUGS, {'page_size': 5}))) == 5
        assert len(results(auth(manager).get(BUGS, {'page_size': 25}))) == 25

    def test_LST_03_page_size_is_capped_at_100(self, auth, manager, project, make_issue):
        for i in range(105):
            make_issue(project, title=f'Bulk {i}')
        assert len(results(auth(manager).get(BUGS, {'page_size': 1000}))) == 100

    def test_LST_04_last_page_has_remaining_rows(self, auth, manager, many):
        assert len(results(auth(manager).get(BUGS, {'page': 3}))) == 5

    def test_LST_05_out_of_range_page_is_404(self, auth, manager, many):
        assert auth(manager).get(BUGS, {'page': 99}).status_code == 404

    def test_LST_06_pages_never_repeat_or_skip_rows(self, auth, manager, many):
        seen = []
        for page in (1, 2, 3):
            seen += [r['id'] for r in results(auth(manager).get(BUGS, {'page': page}))]
        assert len(seen) == 25 and len(set(seen)) == 25

    def test_LST_07_pages_are_stable_when_all_rows_tie_on_sort_key(self, auth, manager, many):
        seen = []
        for page in (1, 2, 3):
            seen += [r['id'] for r in results(auth(manager).get(BUGS, {'page': page, 'ordering': 'severity'}))]
        assert len(set(seen)) == 25

    def test_LST_08_empty_list_is_valid(self, auth, manager, db):
        body = auth(manager).get(BUGS).json()
        assert body['count'] == 0 and body['results'] == []


# -------------------------------------------------------------------- sorting
class TestSorting:
    @pytest.fixture
    def mixed(self, project, make_issue):
        make_issue(project, title='low', severity='LOW', priority='LOW', status='CLOSED')
        make_issue(project, title='crit', severity='CRITICAL', priority='URGENT', status='OPEN')
        make_issue(project, title='trivial', severity='TRIVIAL', priority='MEDIUM', status='QA_TESTING')
        make_issue(project, title='high', severity='HIGH', priority='HIGH', status='IN_PROGRESS')
        make_issue(project, title='medium', severity='MEDIUM', priority='MEDIUM', status='TRIAGED')

    def test_LST_10_severity_sorts_by_importance_not_alphabet(self, auth, manager, mixed):
        assert titles(auth(manager).get(BUGS, {'ordering': 'severity'})) == ['crit', 'high', 'medium', 'low', 'trivial']

    def test_LST_11_severity_descending(self, auth, manager, mixed):
        assert titles(auth(manager).get(BUGS, {'ordering': '-severity'})) == ['trivial', 'low', 'medium', 'high', 'crit']

    def test_LST_12_priority_sorting(self, auth, manager, mixed):
        ordered = titles(auth(manager).get(BUGS, {'ordering': 'priority'}))
        assert ordered[0] == 'crit' and ordered[1] == 'high' and ordered[-1] == 'low'

    def test_LST_13_status_sorts_in_workflow_order(self, auth, manager, mixed):
        assert titles(auth(manager).get(BUGS, {'ordering': 'status'})) == ['crit', 'medium', 'high', 'trivial', 'low']

    def test_LST_14_title_sorting(self, auth, manager, mixed):
        assert titles(auth(manager).get(BUGS, {'ordering': 'title'})) == sorted(['low', 'crit', 'trivial', 'high', 'medium'])

    def test_LST_15_default_order_is_newest_first(self, auth, manager, project, make_issue):
        old = make_issue(project, title='old')
        new = make_issue(project, title='new')
        Issue.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=5))
        assert titles(auth(manager).get(BUGS)) == ['new', 'old']

    def test_LST_16_unknown_ordering_field_is_ignored_not_500(self, auth, manager, mixed):
        response = auth(manager).get(BUGS, {'ordering': 'password'})
        assert response.status_code == 200 and response.json()['count'] == 5

    def test_LST_17_multi_field_ordering(self, auth, manager, project, make_issue):
        make_issue(project, title='b', severity='HIGH')
        make_issue(project, title='a', severity='HIGH')
        make_issue(project, title='c', severity='LOW')
        assert titles(auth(manager).get(BUGS, {'ordering': 'severity,title'})) == ['a', 'b', 'c']


# --------------------------------------------------------------------- search
class TestSearch:
    @pytest.fixture
    def data(self, project, other_project, make_issue, dev, dev2):
        make_issue(project, title='Login crashes on Safari', module='Auth', tags='safari,login', description='Redirect loop', assignee=dev)
        make_issue(project, title='Dashboard chart overlaps', module='Dashboard', tags='ui', description='Legend overlap')
        make_issue(other_project, title='Payment webhook fails', module='Payments', tags='webhook', assignee=dev2)

    def test_LST_20_search_title(self, auth, manager, data):
        assert titles(auth(manager).get(BUGS, {'search': 'crashes'})) == ['Login crashes on Safari']

    def test_LST_21_search_is_case_insensitive(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'search': 'SAFARI'}).json()['count'] == 1

    def test_LST_22_search_description_module_and_tags(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'search': 'redirect'}).json()['count'] == 1
        assert auth(manager).get(BUGS, {'search': 'Dashboard'}).json()['count'] == 1
        assert auth(manager).get(BUGS, {'search': 'webhook'}).json()['count'] == 1

    def test_LST_23_search_assignee_and_reporter_username(self, auth, manager, data):
        assert titles(auth(manager).get(BUGS, {'search': 'dev2'})) == ['Payment webhook fails']
        assert auth(manager).get(BUGS, {'search': 'qa'}).json()['count'] == 3  # qa reported all of them

    def test_LST_24_search_project_key(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'search': 'BET'}).json()['count'] == 1

    def test_LST_25_multiple_words_must_all_match(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'search': 'login safari'}).json()['count'] == 1
        assert auth(manager).get(BUGS, {'search': 'login payment'}).json()['count'] == 0

    def test_LST_26_no_match_returns_empty_list(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'search': 'zzzzzz'}).json()['count'] == 0

    def test_LST_27_lookup_by_ticket_key(self, auth, manager, project, data):
        issue = Issue.objects.get(title='Dashboard chart overlaps')
        assert titles(auth(manager).get(BUGS, {'search': f'ALP-{issue.pk}'})) == ['Dashboard chart overlaps']

    def test_LST_28_ticket_key_with_wrong_project_prefix_finds_nothing(self, auth, manager, data):
        issue = Issue.objects.get(title='Dashboard chart overlaps')
        assert auth(manager).get(BUGS, {'search': f'BET-{issue.pk}'}).json()['count'] == 0

    def test_LST_29_lookup_by_bare_id(self, auth, manager, data):
        issue = Issue.objects.get(title='Login crashes on Safari')
        assert titles(auth(manager).get(BUGS, {'search': str(issue.pk)})) == ['Login crashes on Safari']

    def test_LST_30_search_respects_visibility(self, auth, dev, data):
        assert auth(dev).get(BUGS, {'search': 'payment'}).json()['count'] == 0

    def test_LST_31_sql_injection_attempt_is_harmless(self, auth, manager, data):
        response = auth(manager).get(BUGS, {'search': "'; DROP TABLE issues_issue; --"})
        assert response.status_code == 200 and Issue.objects.count() == 3

    def test_LST_32_search_combines_with_filter_and_ordering(self, auth, manager, project, make_issue):
        make_issue(project, title='login a', severity='LOW')
        make_issue(project, title='login b', severity='CRITICAL')
        make_issue(project, title='other', severity='CRITICAL')
        response = auth(manager).get(BUGS, {'search': 'login', 'severity': 'CRITICAL', 'ordering': 'title'})
        assert titles(response) == ['login b']


# -------------------------------------------------------------------- filters
class TestFilters:
    @pytest.fixture
    def data(self, project, make_issue, dev):
        now = timezone.now()
        a = make_issue(project, title='a', status='OPEN', severity='HIGH', module='Auth', assignee=dev)
        b = make_issue(project, title='b', status='CLOSED', severity='LOW', module='API')
        c = make_issue(project, title='c', status='OPEN', severity='HIGH', module='API', is_duplicate=True, duplicate_of=a)
        Issue.objects.filter(pk=a.pk).update(created_at=now - timedelta(days=10))
        Issue.objects.filter(pk=b.pk).update(created_at=now - timedelta(days=3))
        Issue.objects.filter(pk=c.pk).update(created_at=now - timedelta(days=1))

    def test_LST_40_status_severity_module_filters(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'status': 'OPEN'}).json()['count'] == 2
        assert auth(manager).get(BUGS, {'severity': 'HIGH', 'module': 'api'}).json()['count'] == 1

    def test_LST_41_assignee_filter_and_unassigned(self, auth, manager, dev, data):
        assert titles(auth(manager).get(BUGS, {'assignee': dev.pk})) == ['a']
        assert sorted(titles(auth(manager).get(BUGS, {'unassigned': 'true'}))) == ['b', 'c']

    def test_LST_42_duplicate_filter(self, auth, manager, data):
        assert titles(auth(manager).get(BUGS, {'is_duplicate': 'true'})) == ['c']
        assert auth(manager).get(BUGS, {'is_duplicate': 'false'}).json()['count'] == 2

    def test_LST_43_date_range_filters(self, auth, manager, data):
        today = timezone.now().date()
        after = (today - timedelta(days=5)).isoformat()
        before = (today - timedelta(days=5)).isoformat()
        assert sorted(titles(auth(manager).get(BUGS, {'created_after': after}))) == ['b', 'c']
        assert titles(auth(manager).get(BUGS, {'created_before': before})) == ['a']

    def test_LST_44_invalid_date_returns_400_not_500(self, auth, manager, data):
        assert auth(manager).get(BUGS, {'created_after': 'yesterday'}).status_code == 400

    def test_LST_45_combined_filters_and_pagination_keep_total(self, auth, manager, data):
        body = auth(manager).get(BUGS, {'status': 'OPEN', 'page_size': 1}).json()
        assert body['count'] == 2 and len(body['results']) == 1


# -------------------------------------------------------------------- summary
class TestSummary:
    def test_ISS_30_summary_counts_match_data(self, auth, manager, project, make_issue):
        make_issue(project, status='OPEN', severity='CRITICAL')
        make_issue(project, status='IN_PROGRESS', severity='HIGH')
        make_issue(project, status='CLOSED', severity='LOW')
        body = auth(manager).get(f'{BUGS}summary/').json()
        assert body['total'] == 3 and body['open'] == 1 and body['in_progress'] == 1
        assert body['critical'] == 1 and body['resolved'] == 1
        assert sum(body['by_status'].values()) == 3 and sum(body['by_severity'].values()) == 3

    def test_ISS_31_summary_respects_membership(self, auth, dev, project, other_project, make_issue):
        make_issue(project)
        make_issue(other_project)
        assert auth(dev).get(f'{BUGS}summary/').json()['total'] == 1
