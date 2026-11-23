"""
Milestone 1 QA - registration, login and token handling (test plan IDs: AUTH-xx).
Known defects are marked xfail and reference the defect IDs in docs/qa/M1_QA_Report.md.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

REGISTER = '/api/v1/auth/register/'
LOGIN = '/api/v1/auth/login/'
REFRESH = '/api/v1/auth/token/refresh/'
ME = '/api/v1/auth/me/'
USERS = '/api/v1/auth/users/'


def valid_payload(**overrides):
    data = {
        'username': 'newuser', 'email': 'newuser@bugflow.test',
        'password': 'Str0ng!Pass#2026', 'password_confirm': 'Str0ng!Pass#2026',
        'first_name': 'New', 'last_name': 'User',
    }
    data.update(overrides)
    return data


def login(client, username, password):
    return client.post(LOGIN, {'username': username, 'password': password}, format='json')


# ---------------------------------------------------------------- registration
class TestRegistration:
    def test_AUTH_01_register_success(self, client, db):
        response = client.post(REGISTER, valid_payload(), format='json')
        assert response.status_code == 201
        body = response.json()
        assert body['user']['username'] == 'newuser'
        assert 'password' not in body['user'] and 'password' not in body

    def test_AUTH_02_default_role_is_developer(self, client, db):
        client.post(REGISTER, valid_payload(), format='json')
        assert User.objects.get(username='newuser').role == 'DEVELOPER'

    def test_AUTH_03_password_is_hashed(self, client, db):
        client.post(REGISTER, valid_payload(), format='json')
        stored = User.objects.get(username='newuser').password
        assert stored != 'Str0ng!Pass#2026' and stored.startswith(('pbkdf2_', 'argon2', 'bcrypt'))

    def test_AUTH_04_duplicate_username_rejected(self, client, dev):
        response = client.post(REGISTER, valid_payload(username='dev'), format='json')
        assert response.status_code == 400

    def test_AUTH_05_duplicate_email_rejected(self, client, dev):
        response = client.post(REGISTER, valid_payload(email='dev@bugflow.test'), format='json')
        assert response.status_code == 400

    def test_AUTH_06_password_mismatch_rejected(self, client, db):
        response = client.post(REGISTER, valid_payload(password_confirm='Different!1'), format='json')
        assert response.status_code == 400

    @pytest.mark.parametrize('bad_password', ['123456', 'password', 'abc', '11111111'])
    def test_AUTH_07_weak_passwords_rejected(self, client, db, bad_password):
        response = client.post(REGISTER, valid_payload(password=bad_password, password_confirm=bad_password), format='json')
        assert response.status_code == 400

    @pytest.mark.parametrize('missing', ['username', 'email', 'password', 'password_confirm'])
    def test_AUTH_08_required_fields(self, client, db, missing):
        payload = valid_payload()
        payload.pop(missing)
        assert client.post(REGISTER, payload, format='json').status_code == 400

    def test_AUTH_09_invalid_email_rejected(self, client, db):
        assert client.post(REGISTER, valid_payload(email='not-an-email'), format='json').status_code == 400

    def test_AUTH_10_invalid_role_rejected(self, client, db):
        assert client.post(REGISTER, valid_payload(role='SUPERHERO'), format='json').status_code == 400

    def test_AUTH_11_cannot_self_register_as_admin(self, client, db):
        client.post(REGISTER, valid_payload(role='ADMIN'), format='json')
        user = User.objects.get(username='newuser')
        assert user.role != 'ADMIN'

    def test_AUTH_12_cannot_self_register_as_manager(self, client, db):
        client.post(REGISTER, valid_payload(role='MANAGER'), format='json')
        assert User.objects.get(username='newuser').role != 'MANAGER'


# ----------------------------------------------------------------------- login
class TestLogin:
    def test_AUTH_20_login_success_returns_tokens_and_role(self, client, dev, password):
        response = login(client, 'dev', password)
        assert response.status_code == 200
        body = response.json()
        assert body['access'] and body['refresh']
        assert body['user']['role'] == 'DEVELOPER'
        assert body['user']['username'] == 'dev'

    def test_AUTH_21_wrong_password_401(self, client, dev):
        assert login(client, 'dev', 'WrongPass!1').status_code == 401

    def test_AUTH_22_unknown_user_401(self, client, db):
        assert login(client, 'ghost', 'Whatever!1').status_code == 401

    def test_AUTH_23_same_error_for_unknown_user_and_wrong_password(self, client, dev):
        """Error text must not reveal whether the username exists."""
        wrong_pw = login(client, 'dev', 'WrongPass!1').json()
        unknown = login(client, 'ghost', 'WrongPass!1').json()
        assert wrong_pw == unknown

    def test_AUTH_24_inactive_user_cannot_login(self, client, dev, password):
        dev.is_active = False
        dev.save()
        assert login(client, 'dev', password).status_code == 401

    def test_AUTH_25_blank_credentials_400(self, client, db):
        assert client.post(LOGIN, {}, format='json').status_code == 400

    def test_AUTH_26_login_response_has_no_password(self, client, dev, password):
        assert 'password' not in login(client, 'dev', password).json()['user']


# ---------------------------------------------------------- tokens & protection
class TestTokens:
    def test_AUTH_30_protected_endpoint_requires_token(self, client, db):
        assert client.get(ME).status_code == 401
        assert client.get('/api/v1/bugs/').status_code == 401
        assert client.get('/api/v1/projects/').status_code == 401

    def test_AUTH_31_garbage_token_rejected(self, client, db):
        client.credentials(HTTP_AUTHORIZATION='Bearer not.a.token')
        assert client.get(ME).status_code == 401

    def test_AUTH_32_tampered_token_rejected(self, client, dev, password):
        access = login(client, 'dev', password).json()['access']
        head, payload, signature = access.split('.')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {head}.{payload}.{signature[:-3]}abc')
        assert client.get(ME).status_code == 401

    def test_AUTH_33_valid_token_grants_access(self, client, dev, password):
        access = login(client, 'dev', password).json()['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = client.get(ME)
        assert response.status_code == 200 and response.json()['username'] == 'dev'

    def test_AUTH_34_refresh_returns_new_access_token(self, client, dev, password):
        refresh = login(client, 'dev', password).json()['refresh']
        response = client.post(REFRESH, {'refresh': refresh}, format='json')
        assert response.status_code == 200 and response.json()['access']

    def test_AUTH_35_access_token_cannot_be_used_as_refresh(self, client, dev, password):
        access = login(client, 'dev', password).json()['access']
        assert client.post(REFRESH, {'refresh': access}, format='json').status_code == 401

    def test_AUTH_36_wrong_scheme_rejected(self, client, dev, password):
        access = login(client, 'dev', password).json()['access']
        client.credentials(HTTP_AUTHORIZATION=f'Token {access}')
        assert client.get(ME).status_code == 401

    def test_AUTH_37_refresh_blocked_after_user_deactivated(self, client, dev, password):
        refresh = login(client, 'dev', password).json()['refresh']
        dev.is_active = False
        dev.save()
        assert client.post(REFRESH, {'refresh': refresh}, format='json').status_code == 401


# -------------------------------------------------------------------- profile
class TestProfile:
    def test_AUTH_40_me_returns_own_profile(self, auth, dev):
        body = auth(dev).get(ME).json()
        assert body['username'] == 'dev' and body['role'] == 'DEVELOPER'

    def test_AUTH_41_can_update_own_department(self, auth, dev):
        response = auth(dev).patch(ME, {'department': 'Platform'}, format='json')
        assert response.status_code == 200
        dev.refresh_from_db()
        assert dev.department == 'Platform'

    def test_AUTH_42_cannot_change_own_role(self, auth, dev):
        auth(dev).patch(ME, {'role': 'ADMIN'}, format='json')
        dev.refresh_from_db()
        assert dev.role == 'DEVELOPER'

    def test_AUTH_43_user_list_requires_login(self, client, db):
        assert client.get(USERS).status_code == 401

    def test_AUTH_44_user_list_returns_users(self, auth, dev, qa):
        response = auth(dev).get(USERS)
        assert response.status_code == 200
        names = {u['username'] for u in response.json()['results']}
        assert {'dev', 'qa'} <= names

    def test_AUTH_45_user_list_role_filter_works(self, auth, dev, qa, manager):
        response = auth(dev).get(USERS, {'role': 'QA'})
        roles = {u['role'] for u in response.json()['results']}
        assert roles == {'QA'}
