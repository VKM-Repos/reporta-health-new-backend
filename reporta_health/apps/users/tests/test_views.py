"""
Tests for authentication and user profile endpoints.

Endpoints under test:
    POST   /api/auth/users/                  — register (djoser)
    POST   /api/auth/jwt/create/             — login
    POST   /api/auth/jwt/refresh/            — refresh access token
    POST   /api/auth/jwt/verify/             — verify token
    POST   /api/auth/users/reset_password/   — request password reset
    GET    /api/users/me/                    — get current user profile
    PATCH  /api/users/me/                    — update profile (UserUpdateSerializer)
    GET    /api/users/me/reviews/            — current user's reviews
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_tokens(api_client, user):
    """Log in and return access + refresh tokens."""
    response = api_client.post('/api/auth/jwt/create/', {
        'email': user.email,
        'password': 'testpass123',
    })
    return response.data


# ---------------------------------------------------------------------------
# Registration  POST /api/auth/users/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserRegistration:

    URL = '/api/auth/users/'

    def valid_payload(self, **overrides):
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'Ada',
            'last_name': 'Lovelace',
            'password': 'StrongPass123!',
            're_password': 'StrongPass123!',
        }
        data.update(overrides)
        return data

    def test_valid_registration_returns_201(self, api_client):
        response = api_client.post(self.URL, self.valid_payload())
        assert response.status_code == 201

    def test_registration_creates_user_in_db(self, api_client):
        api_client.post(self.URL, self.valid_payload())
        assert User.objects.filter(email='newuser@example.com').exists()

    def test_response_contains_email_and_username(self, api_client):
        response = api_client.post(self.URL, self.valid_payload())
        assert response.data['email'] == 'newuser@example.com'
        assert response.data['username'] == 'newuser'

    def test_optional_phone_number_accepted(self, api_client):
        response = api_client.post(
            self.URL, self.valid_payload(phone_number='+2348012345678')
        )
        assert response.status_code == 201

    def test_password_not_in_response(self, api_client):
        response = api_client.post(self.URL, self.valid_payload())
        assert 'password' not in response.data

    def test_duplicate_email_returns_400(self, api_client, user):
        response = api_client.post(
            self.URL, self.valid_payload(email=user.email, username='someone_new')
        )
        assert response.status_code == 400

    def test_mismatched_passwords_returns_400(self, api_client):
        response = api_client.post(
            self.URL, self.valid_payload(re_password='DoesNotMatch!')
        )
        assert response.status_code == 400

    def test_weak_password_returns_400(self, api_client):
        response = api_client.post(
            self.URL, self.valid_payload(password='123', re_password='123')
        )
        assert response.status_code == 400

    def test_missing_email_returns_400(self, api_client):
        payload = self.valid_payload()
        del payload['email']
        response = api_client.post(self.URL, payload)
        assert response.status_code == 400

    def test_missing_username_returns_400(self, api_client):
        payload = self.valid_payload()
        del payload['username']
        response = api_client.post(self.URL, payload)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login  POST /api/auth/jwt/create/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogin:

    URL = '/api/auth/jwt/create/'

    def test_valid_credentials_returns_200(self, api_client, user):
        response = api_client.post(self.URL, {
            'email': user.email,
            'password': 'testpass123',
        })
        assert response.status_code == 200

    def test_response_has_access_and_refresh_tokens(self, api_client, user):
        response = api_client.post(self.URL, {
            'email': user.email,
            'password': 'testpass123',
        })
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_wrong_password_returns_401(self, api_client, user):
        response = api_client.post(self.URL, {
            'email': user.email,
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_nonexistent_email_returns_401(self, api_client):
        response = api_client.post(self.URL, {
            'email': 'ghost@example.com',
            'password': 'testpass123',
        })
        assert response.status_code == 401

    def test_missing_password_returns_400(self, api_client, user):
        response = api_client.post(self.URL, {'email': user.email})
        assert response.status_code == 400

    def test_inactive_user_cannot_login(self, api_client, user_factory):
        inactive = user_factory(is_active=False)
        response = api_client.post(self.URL, {
            'email': inactive.email,
            'password': 'testpass123',
        })
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh  POST /api/auth/jwt/refresh/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenRefresh:

    URL = '/api/auth/jwt/refresh/'

    def test_valid_refresh_token_returns_200(self, api_client, user):
        tokens = get_tokens(api_client, user)
        response = api_client.post(self.URL, {'refresh': tokens['refresh']})
        assert response.status_code == 200

    def test_returns_new_access_token(self, api_client, user):
        tokens = get_tokens(api_client, user)
        response = api_client.post(self.URL, {'refresh': tokens['refresh']})
        assert 'access' in response.data

    def test_invalid_token_returns_401(self, api_client):
        response = api_client.post(self.URL, {'refresh': 'not.a.valid.token'})
        assert response.status_code == 401

    def test_missing_token_returns_400(self, api_client):
        response = api_client.post(self.URL, {})
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Token verify  POST /api/auth/jwt/verify/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenVerify:

    URL = '/api/auth/jwt/verify/'

    def test_valid_access_token_returns_200(self, api_client, user):
        tokens = get_tokens(api_client, user)
        response = api_client.post(self.URL, {'token': tokens['access']})
        assert response.status_code == 200

    def test_invalid_token_returns_401(self, api_client):
        response = api_client.post(self.URL, {'token': 'garbage.token.here'})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Password reset  POST /api/auth/users/reset_password/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPasswordReset:

    URL = '/api/auth/users/reset_password/'

    def test_known_email_returns_204(self, api_client, user):
        response = api_client.post(self.URL, {'email': user.email})
        assert response.status_code == 204

    def test_unknown_email_also_returns_204(self, api_client):
        # Djoser must not reveal whether an email exists — security requirement
        response = api_client.post(self.URL, {'email': 'ghost@example.com'})
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Current user profile  GET/PATCH/PUT  /api/users/me/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCurrentUserProfile:

    URL = '/api/users/me/'

    # --- GET ---

    def test_authenticated_returns_200(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == 200

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_response_has_all_userserializer_fields(self, auth_client, user):
        response = auth_client.get(self.URL)
        for field in (
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'bio', 'is_verified',
            'review_count', 'date_joined',
        ):
            assert field in response.data, f"Missing field: {field}"

    def test_returns_correct_email(self, auth_client, user):
        response = auth_client.get(self.URL)
        assert response.data['email'] == user.email

    def test_full_name_matches_get_full_name(self, auth_client, user):
        response = auth_client.get(self.URL)
        assert response.data['full_name'] == user.get_full_name()

    def test_review_count_is_zero_with_no_reviews(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.data['review_count'] == 0

    def test_password_not_exposed(self, auth_client):
        response = auth_client.get(self.URL)
        assert 'password' not in response.data

    # --- PATCH (only UserUpdateSerializer fields accepted) ---

    def test_patch_first_name_returns_200(self, auth_client):
        response = auth_client.patch(self.URL, {'first_name': 'Chioma'})
        assert response.status_code == 200

    def test_patch_first_name_persists_to_db(self, auth_client, user):
        auth_client.patch(self.URL, {'first_name': 'Chioma'})
        user.refresh_from_db()
        assert user.first_name == 'Chioma'

    def test_patch_last_name_persists_to_db(self, auth_client, user):
        auth_client.patch(self.URL, {'last_name': 'Okonkwo'})
        user.refresh_from_db()
        assert user.last_name == 'Okonkwo'

    def test_patch_phone_number_persists_to_db(self, auth_client, user):
        auth_client.patch(self.URL, {'phone_number': '+2348099887766'})
        user.refresh_from_db()
        assert user.phone_number == '+2348099887766'

    def test_patch_bio_persists_to_db(self, auth_client, user):
        auth_client.patch(self.URL, {'bio': 'Healthcare advocate based in Lagos.'})
        user.refresh_from_db()
        assert user.bio == 'Healthcare advocate based in Lagos.'

    def test_patch_email_is_silently_ignored(self, auth_client, user):
        # email is not in UserUpdateSerializer so it should be ignored
        original = user.email
        auth_client.patch(self.URL, {'email': 'hacked@example.com'})
        user.refresh_from_db()
        assert user.email == original

    def test_patch_is_verified_is_silently_ignored(self, auth_client, user):
        # Users must not be able to self-verify
        original = user.is_verified
        auth_client.patch(self.URL, {'is_verified': True})
        user.refresh_from_db()
        assert user.is_verified == original

    # --- PUT ---

    def test_put_with_update_fields_returns_200(self, auth_client):
        payload = {
            'first_name': 'New',
            'last_name': 'Name',
            'phone_number': '+2348011111111',
            'bio': 'Updated bio.',
        }
        response = auth_client.put(self.URL, payload)
        assert response.status_code == 200

    # --- Isolation: each user only sees their own profile ---

    def test_each_user_sees_their_own_profile(self, api_client, user_factory):
        user_a = user_factory()
        user_b = user_factory()

        api_client.force_authenticate(user=user_a)
        response = api_client.get(self.URL)
        assert response.data['email'] == user_a.email
        assert response.data['email'] != user_b.email


# ---------------------------------------------------------------------------
# Current user reviews  GET /api/users/me/reviews/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCurrentUserReviews:

    URL = '/api/users/me/reviews/'

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == 200

    def test_empty_when_no_reviews(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_only_returns_current_users_reviews(
        self, auth_client, user, facility, review_factory, user_factory, facility_factory, lagos_point
    ):
        review_factory(user=user, facility=facility)

        other_user = user_factory()
        other_facility = facility_factory(location=lagos_point)
        review_factory(user=other_user, facility=other_facility)

        response = auth_client.get(self.URL)
        assert response.data['count'] == 1

    def test_count_matches_number_of_reviews(
        self, auth_client, user, facility_factory, review_factory, lagos_point
    ):
        f1 = facility_factory(location=lagos_point)
        f2 = facility_factory(location=lagos_point)
        review_factory(user=user, facility=f1)
        review_factory(user=user, facility=f2)

        response = auth_client.get(self.URL)
        assert response.data['count'] == 2

    def test_response_is_paginated(self, auth_client):
        response = auth_client.get(self.URL)
        assert 'count' in response.data
        assert 'results' in response.data
        assert 'next' in response.data