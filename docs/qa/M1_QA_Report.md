# BugFlow - Milestone 1 QA Report

**Tester:** Nandhini | **Date:** 21 Nov 2026
**Build:** `main` @ `9749027` (Ziyan, Week 1) + `feature/nandhini-m1-qa-backend`
**Scope:** backend API (the frontend and `ai_triage` code are not in the repo yet, so they were not tested)

## 1. Result at a glance

| | |
|---|---|
| Tests run | 157 |
| Passed | 147 |
| Known defects (expected failures) | 10 tests covering **8 defects** |
| Unexpected failures | 0 |

**Milestone 1 exit criteria**

| Criterion (from the brief) | Status | Notes |
|---|---|---|
| Authentication and authorization enforce access controls with **zero critical security violations** | **NOT MET** | Two Critical defects (D-01, D-02): any user can become ADMIN. Both are small fixes. |
| Issue lifecycle tracked with >= 99% workflow consistency | Partial | Only the "cannot close straight from Open" rule exists. The full state machine is Week 3, so the 99% figure cannot be measured yet. Existing rule and `resolved_at` handling pass. |
| Initial issue reports generated for all projects | Met (API) | `/bugs/summary/` returns correct counts, per project and overall. The dashboard UI is not in the repo yet. |

## 2. Defects

| ID | Severity | Area | Owner |
|---|---|---|---|
| D-01 | **Critical** | Registration | Ziyan |
| D-02 | **Critical** | Profile | Ziyan |
| D-03 | **High** | Issue detail | Ziyan |
| D-04 | Medium | Issue summary | Ziyan |
| D-05 | Low | User list | Ziyan |
| D-06 | Medium | Issue update | Ziyan |
| D-07 | Medium | Issue assignment | Ziyan (Week 3 assignment endpoints) |
| D-08 | Medium | Role rules | Ziyan (Week 2 RBAC task) |

### D-01 (Critical): anyone can register as ADMIN or MANAGER
- **Steps:** `POST /api/v1/auth/register/` with `"role": "ADMIN"` and no token.
- **Actual:** the account is created with the ADMIN role. Admins and managers see every project, create projects, manage members and delete issues.
- **Expected:** public registration always creates a DEVELOPER (or the lowest role); roles are changed only by an admin.
- **Fix:** in `UserRegistrationSerializer` make `role` read-only (`extra_kwargs = {'role': {'read_only': True}}`) and keep `role = DEVELOPER` in `create()`.
- **Tests:** `test_AUTH_11`, `test_AUTH_12`

### D-02 (Critical): any user can promote themselves through their profile
- **Steps:** log in as a developer, then `PATCH /api/v1/auth/me/` with `{"role": "ADMIN"}`.
- **Actual:** the role changes to ADMIN (the token claim updates on the next login).
- **Fix:** add `'role'` to `read_only_fields` in `UserDetailSerializer` (or use a separate serializer for profile edits with only `first_name`, `last_name`, `department`).
- **Test:** `test_AUTH_42`

### D-03 (High): issues of other projects can be read and edited
- **Steps:** as a developer who is not in project B, `GET` or `PATCH /api/v1/bugs/<id>/` for an issue in project B.
- **Actual:** 200 and the change is saved. The list endpoint hides these issues, but the detail endpoint does not.
- **Expected:** 404 for non-members (same rule as the list).
- **Fix:** in `IssueDetailView` use a `get_queryset()` that applies the same membership filter as `IssueListCreateView`.
- **Tests:** `test_SEC_01`, `test_SEC_02`

### D-04 (Medium): summary counts leak for any project
- **Steps:** `GET /api/v1/bugs/summary/?project=<id of a project you are not in>`.
- **Actual:** real counts are returned. The membership filter is skipped whenever `project` is given.
- **Fix:** always apply the membership filter first, then the optional `project` filter.
- **Test:** `test_SEC_03`

### D-05 (Low): `?role=` / `?department=` filters on the user list do nothing
- **Cause:** `UserListView` declares `filterset_fields`, but `django_filters` is not in `INSTALLED_APPS` and no filter backend is configured, so it is silently ignored. The assignee picker in the UI would show every user.
- **Fix:** add `'django_filters'` to `INSTALLED_APPS` and `filter_backends = [DjangoFilterBackend]` on the view.
- **Test:** `test_AUTH_45`

### D-06 (Medium): `resolved_at` can be set by the client
- **Steps:** `PATCH /api/v1/bugs/<id>/` with `{"resolved_at": "2020-01-01T00:00:00Z"}` on an open issue.
- **Actual:** accepted, which can distort resolution-time and fix-rate analytics later.
- **Fix:** remove `resolved_at` from `IssueUpdateSerializer.fields`; the view already sets it when status becomes CLOSED.
- **Test:** `test_SEC_04`

### D-07 (Medium): issues can be assigned to people outside the project
- **Steps:** create or update an issue with `assignee` set to a user who is not a member of the project.
- **Actual:** accepted. That user then cannot even open the issue through the list (but can through D-03).
- **Fix:** validate that the assignee is a project member in the create/update serializers and in the Week 3 assignment endpoints.
- **Test:** `test_SEC_05`

### D-08 (Medium, expected): developers can close issues
- **Actual:** any user with access can set any status. The brief says QA verifies and closes.
- **Status:** this is Ziyan's Week 2 RBAC task, so it is flagged for retest rather than as a surprise. Retest after that merge.
- **Test:** `test_SEC_06`

## 3. Fixed or added in this branch

**Projects and membership (`collab`, my module)**
- Project detail is now limited to members and Managers/Admins; non-members get 404 (previously any user could open any project)
- New `GET /projects/<id>/members/` lists members
- Removing the only Project Lead is blocked (400)
- Project key is validated and normalised to uppercase (2-10 characters, letters and digits)
- Project list queries are pre-loaded and no longer grow with the number of projects (N+1 removed)

**Issue list (Week 2)**
- Pagination with `page_size` (default 10, maximum 100)
- `severity`, `priority` and `status` sort by importance / workflow order instead of alphabetically (alphabetical put Critical, High, Low, Medium, Trivial)
- A stable tie-break so pages never repeat or skip rows
- Search now also covers reporter, assignee, project name and key, and jumps to a ticket by `BF-12` or `12`
- New filters: `module`, `created_after`, `created_before`, `unassigned`, `is_duplicate`
- These live in `apps/issues/listing.py`; `issues/views.py` changed by about 15 lines (imports and the list view's filter settings only) to keep merges with Ziyan simple

**Other**
- `python manage.py seed_data` (5 users, 2 projects, 50 bugs, repeatable, `--flush` to reset)
- 157 automated tests, `pytest.ini` and shared fixtures
- Postman collection extended with the new endpoints

## 4. Observations (not tested as defects, worth a decision)

| ID | Observation | Suggestion |
|---|---|---|
| N-01 | `DEBUG` defaults to `True`, `CORS_ALLOW_ALL_ORIGINS` follows it, and `SECRET_KEY` has a hard-coded fallback | Fail on startup if `SECRET_KEY` is missing and `DEBUG` is off; set `DEBUG=False` in the production compose file |
| N-02 | Minimum password length is 6 | Raise to 8 or more |
| N-03 | No rate limiting on login | Add DRF throttling for `/auth/login/` before UAT |
| N-04 | Any logged-in user can list all users with their emails | Limit to Managers/Admins, or return only id, name and role for assignee pickers |
| N-05 | Tested on SQLite; the PostgreSQL path (`USE_SQLITE=False`) was not run here | Naren's Docker setup should run the same suite against PostgreSQL |
| N-06 | `ai_triage` and the frontend are empty or absent in the repo | Test them as they land (auto-tag, duplicate search, login screens) |

## 5. Retest plan

1. Ziyan fixes D-01 and D-02 first (both are about three lines). Rerun `pytest -m defect -rxX`; the matching tests change to XPASS.
2. After Ziyan's Week 2 RBAC merge, retest D-03, D-04, D-06 and D-08.
3. Once these pass, delete the `xfail` markers so any regression fails CI.
4. Run the manual checklist in the test plan when the UI is available.
