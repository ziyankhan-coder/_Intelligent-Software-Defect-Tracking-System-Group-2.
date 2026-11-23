# BugFlow - Milestone 1 QA Test Plan

**Owner:** Nandhini (Backend Support & QA Lead)
**Scope:** Milestone 1 (Weeks 1-2) - authentication, role-based access, projects and membership, issue creation/list, admin panel
**Build under test:** `main` @ `9749027` (Ziyan, Week 1) plus the Week 1-2 changes on `feature/nandhini-m1-qa-backend`

## 1. Objectives

Show that Milestone 1 meets the evaluation criteria in the project brief:

| # | Criterion | How it is checked |
|---|---|---|
| 1 | Issue lifecycle events tracked with >= 99% workflow consistency | ISS-08, ISS-09 (state rules); full state machine is Week 3 |
| 2 | Access controls enforced, **zero critical security violations** | AUTH, PRJ, MEM, SEC groups |
| 3 | Initial issue reports generated for all configured projects | ISS-30, ISS-31 (`/bugs/summary/`) |

## 2. Approach

- **Automated API tests** (pytest + pytest-django, in `backend/apps/*/tests/`). Every test has a plan ID in its name, e.g. `test_AUTH_21_wrong_password_401`.
- **Manual / Postman checks** for anything that needs a running UI (Section 6). The UI is not in the repo yet, so these start when Ramya pushes the frontend.
- **Known defects** are written as tests that assert the *correct* behaviour and are marked `xfail`. They stay visible in every test run until fixed. When a defect is fixed its test starts passing (XPASS) and the marker is removed.

## 3. Test environment

- Python 3.13, Django 5.2, DRF 3.x, SimpleJWT 5.5, SQLite (default `USE_SQLITE=True`) in an isolated test database
- Test data: fixtures in `backend/conftest.py` (admin, manager, two developers, QA; two projects)
- Demo data for manual testing: `python manage.py seed_data` (5 users, 2 projects, 50 bugs; password `BugFlow@2026`)

Run everything:

```bash
cd backend
pip install -r requirements.txt
pytest                      # all tests
pytest -m defect -rxX       # only the known-defect tests
pytest apps/issues -k LST   # one area
```

## 4. Roles used

| Role | Expected capabilities |
|---|---|
| ADMIN / MANAGER | See all projects and issues; create/edit/delete projects; manage members; delete issues |
| DEVELOPER | See and work on issues only in projects they belong to |
| QA | Same visibility as developer; verifies fixes |
| Anonymous | No access to any API except register, login, token refresh and the API root |

## 5. Test cases (automated)

| Area | IDs | What is covered | Tests |
|---|---|---|---|
| Registration | AUTH-01 to AUTH-12 | success, default role, hashed password, duplicate username/email, password mismatch, weak passwords, missing fields, bad email/role, **role self-assignment** | 18 |
| Login | AUTH-20 to AUTH-26 | tokens + role returned, wrong password, unknown user, identical error messages, inactive user, blank body | 7 |
| Tokens | AUTH-30 to AUTH-37 | no/garbage/tampered token, wrong scheme, refresh, access-as-refresh, refresh after deactivation | 8 |
| Profile & users | AUTH-40 to AUTH-45 | own profile, update, **role change**, user list, role filter | 6 |
| Admin panel | ADM-01 to ADM-05 | list pages, search, filters, membership inline, non-staff blocked | 13 |
| Projects | PRJ-01 to PRJ-23 | create (roles, key rules, duplicates), visibility per role, 404 for non-members, counts, query count (N+1), update/delete permissions | 25 |
| Membership | MEM-01 to MEM-17 | list, add, change role, invalid user/role, permissions, remove, last-lead protection, anonymous | 18 |
| Issue create/edit | ISS-01 to ISS-10 | member vs non-member, defaults, validation, reporter, close rule, `resolved_at`, delete permission | 13 |
| Issue visibility | ISS-20 to ISS-23 | project isolation, manager sees all, filter cannot bypass, login required | 4 |
| Pagination | LST-01 to LST-08 | default 10, `page_size`, cap 100, last page, bad page, no repeats/skips, empty list | 8 |
| Sorting | LST-10 to LST-17 | severity/priority/status by rank, descending, title, default newest, unknown field, multi-field | 8 |
| Search | LST-20 to LST-32 | all fields, case, multi-word, ticket key (`BF-12`) and id, project key, visibility, SQL-injection string | 13 |
| Filters | LST-40 to LST-45 | status, severity, module, assignee, unassigned, duplicates, date range, invalid date | 6 |
| Summary | ISS-30, ISS-31 | dashboard counts, membership | 2 |
| Access control | SEC-01 to SEC-08 | non-member read/edit, summary leak, forged `resolved_at`, assignee not in project, developer closing, reporter spoofing, QA delete | 8 |

## 6. Manual checklist (needs the frontend)

To be run once Ramya's UI is in the repo, with the seed data loaded.

- [ ] Register a new user from the UI; confirm login works and the role badge shows in the header
- [ ] Unauthenticated visit to a protected route redirects to `/login`
- [ ] Log in as each role (QA, developer, manager, admin) and confirm the navigation matches the role
- [ ] Log out and use the browser Back button: protected pages must not show data
- [ ] Create a bug with every field filled, then with only the required fields
- [ ] Create a bug with an over-long title (300+ chars) and with HTML/script text; confirm it is rejected or shown as plain text
- [ ] Issue table: search, each filter, sort by severity, change page and page size
- [ ] Dashboard summary cards match the table counts for the same project
- [ ] Switch projects as a developer: only member projects are offered
- [ ] Token expiry: leave the session idle past 60 minutes; confirm refresh or a clean redirect to login
- [ ] Chrome, Edge and Firefox at desktop and phone widths

## 7. Entry and exit criteria

- **Entry:** migrations apply cleanly, `manage.py check` is clean, seed data loads.
- **Exit for Milestone 1:** all non-defect tests pass; no open Critical or High defects; every open defect has an owner and a retest date.

## 8. Defect handling

Defects are recorded in `docs/qa/M1_QA_Report.md` with an ID (D-nn), severity, steps, expected/actual result, owner and suggested fix. Severity: **Critical** = privilege escalation or data exposure across users; **High** = broken access control within normal use; **Medium** = integrity or reliability problem; **Low** = minor or cosmetic.
