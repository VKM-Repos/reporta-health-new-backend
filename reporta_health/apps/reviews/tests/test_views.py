"""
Tests for reviews app.

Endpoints under test:
    GET    /api/facilities/<facility_id>/reviews/           — list facility reviews
    POST   /api/facilities/<facility_id>/reviews/create/    — create review (auth)
    GET    /api/reviews/<id>/                               — review detail
    PUT    /api/reviews/<id>/update/                        — update own review
    PATCH  /api/reviews/<id>/update/                        — partial update own review
    DELETE /api/reviews/<id>/delete/                        — delete own review
    POST   /api/reviews/<review_id>/images/                 — upload image (auth)
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def facility_reviews_url(facility_id):
    return f'/api/v1/facilities/{facility_id}/reviews/'


def facility_reviews_create_url(facility_id):
    return f'/api/v1/facilities/{facility_id}/reviews/create/'


def review_detail_url(pk):
    return f'/api/v1/reviews/{pk}/'


def review_update_url(pk):
    return f'/api/v1/reviews/{pk}/update/'


def review_delete_url(pk):
    return f'/api/v1/reviews/{pk}/delete/'


def review_images_url(review_id):
    return f'/api/v1/reviews/{review_id}/images/'


def create_review_payload(**overrides):
    data = {
        'rating': 4,
        'body': 'This is a test review body with enough content.',
        'is_anonymous': False,
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Facility Review List  GET /api/facilities/<facility_id>/reviews/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityReviewList:

    def test_anonymous_user_can_list_reviews(self, api_client, facility):
        response = api_client.get(facility_reviews_url(facility.pk))
        assert response.status_code == 200

    def test_authenticated_user_can_list_reviews(self, auth_client, facility):
        response = auth_client.get(facility_reviews_url(facility.pk))
        assert response.status_code == 200

    def test_returns_paginated_response(self, api_client, facility):
        response = api_client.get(facility_reviews_url(facility.pk))
        assert 'count' in response.data
        assert 'results' in response.data

    def test_returns_empty_when_no_reviews(self, api_client, facility):
        response = api_client.get(facility_reviews_url(facility.pk))
        assert response.data['count'] == 0

    def test_returns_only_reviews_for_that_facility(
        self, api_client, facility, facility_factory, user, review_factory, lagos_point
    ):
        other_facility = facility_factory(location=lagos_point)
        review_factory(user=user, facility=facility, rating=5)
        review_factory(user=user, facility=other_facility, rating=3)

        response = api_client.get(facility_reviews_url(facility.pk))
        assert response.data['count'] == 1

    def test_review_fields_present(self, api_client, facility, user, review_factory):
        review_factory(user=user, facility=facility)
        response = api_client.get(facility_reviews_url(facility.pk))
        result = response.data['results'][0]
        for field in (
            'id', 'facility', 'facility_name', 'user', 'rating',
            'body', 'is_anonymous', 'helpful_count', 'created_at',
        ):
            assert field in result, f"Missing field: {field}"

    def test_filter_by_rating(self, api_client, facility, user_factory, review_factory):
        u1 = user_factory()
        u2 = user_factory()
        review_factory(user=u1, facility=facility, rating=5)
        review_factory(user=u2, facility=facility, rating=2)

        response = api_client.get(facility_reviews_url(facility.pk), {'rating': 5})
        for r in response.data['results']:
            assert r['rating'] == 5

    def test_ordering_by_created_at(self, api_client, facility, user_factory, review_factory):
        u1 = user_factory()
        u2 = user_factory()
        review_factory(user=u1, facility=facility)
        review_factory(user=u2, facility=facility)

        response = api_client.get(
            facility_reviews_url(facility.pk), {'ordering': '-created_at'}
        )
        assert response.status_code == 200

    def test_nonexistent_facility_returns_empty(self, api_client):
        response = api_client.get(facility_reviews_url(99999))
        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_anonymous_review_included_in_list(self, api_client, facility, user, review_factory):
        review_factory(user=user, facility=facility, is_anonymous=True)
        response = api_client.get(facility_reviews_url(facility.pk))
        assert response.data['count'] == 1

    def test_user_info_is_nested_object(self, api_client, facility, user, review_factory):
        review_factory(user=user, facility=facility)
        response = api_client.get(facility_reviews_url(facility.pk))
        result = response.data['results'][0]
        assert isinstance(result['user'], dict)


# ---------------------------------------------------------------------------
# Create Review  POST /api/facilities/<facility_id>/reviews/create/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReviewCreate:

    def test_authenticated_user_can_create_review(self, auth_client, facility):
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        assert response.status_code == 201

    def test_unauthenticated_user_cannot_create_review(self, api_client, facility):
        response = api_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        assert response.status_code == 401

    def test_create_persists_to_db(self, auth_client, facility):
        from apps.reviews.models import Review
        count_before = Review.objects.count()
        auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        assert Review.objects.count() == count_before + 1

    def test_user_set_from_request(self, auth_client, user, facility):
        auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        from apps.reviews.models import Review
        review = Review.objects.filter(facility=facility).first()
        assert review.user == user

    def test_facility_set_from_url(self, auth_client, facility):
        auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        from apps.reviews.models import Review
        review = Review.objects.filter(facility=facility).first()
        assert review.facility == facility

    def test_response_contains_review_fields(self, auth_client, facility):
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        for field in ('id', 'rating', 'body', 'facility', 'created_at'):
            assert field in response.data, f"Missing field: {field}"

    def test_duplicate_review_is_allowed(self, auth_client, facility, user, review_factory):
        review_factory(user=user, facility=facility)
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload()
        )
        assert response.status_code == 201

    def test_missing_rating_returns_400(self, auth_client, facility):
        payload = create_review_payload()
        del payload['rating']
        response = auth_client.post(facility_reviews_create_url(facility.pk), payload)
        assert response.status_code == 400

    def test_missing_body_returns_400(self, auth_client, facility):
        payload = create_review_payload()
        del payload['body']
        response = auth_client.post(facility_reviews_create_url(facility.pk), payload)
        assert response.status_code == 400

    def test_rating_below_1_returns_400(self, auth_client, facility):
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload(rating=0)
        )
        assert response.status_code == 400

    def test_rating_above_5_returns_400(self, auth_client, facility):
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload(rating=6)
        )
        assert response.status_code == 400

    def test_anonymous_review_accepted(self, auth_client, facility):
        response = auth_client.post(
            facility_reviews_create_url(facility.pk),
            create_review_payload(is_anonymous=True)
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Review Detail  GET /api/reviews/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReviewDetail:

    def test_anonymous_user_can_view_detail(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        assert response.status_code == 200

    def test_returns_correct_review(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        assert response.data['id'] == review.pk

    def test_nonexistent_review_returns_404(self, api_client):
        response = api_client.get(review_detail_url(99999))
        assert response.status_code == 404

    def test_detail_fields_present(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        for field in (
            'id', 'facility', 'facility_name', 'user', 'rating',
            'body', 'is_anonymous', 'is_published', 'flag_count',
            'helpful_count', 'images', 'created_at', 'updated_at',
        ):
            assert field in response.data, f"Missing field: {field}"

    def test_images_is_a_list(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        assert isinstance(response.data['images'], list)

    def test_user_info_is_nested(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        assert isinstance(response.data['user'], dict)

    def test_facility_name_matches(self, api_client, review):
        response = api_client.get(review_detail_url(review.pk))
        assert response.data['facility_name'] == review.facility.name


# ---------------------------------------------------------------------------
# Review Update  PUT/PATCH /api/reviews/<id>/update/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReviewUpdate:

    def test_owner_can_patch_review(self, auth_client, user, facility, review_factory):
        review = review_factory(user=user, facility=facility)
        response = auth_client.patch(review_update_url(review.pk), {'rating': 3})
        assert response.status_code == 200

    def test_patch_rating_persists_to_db(self, auth_client, user, facility, review_factory):
        review = review_factory(user=user, facility=facility, rating=4)
        auth_client.patch(review_update_url(review.pk), {'rating': 2})
        review.refresh_from_db()
        assert review.rating == 2

    def test_patch_body_persists_to_db(self, auth_client, user, facility, review_factory):
        review = review_factory(user=user, facility=facility)
        auth_client.patch(review_update_url(review.pk), {'body': 'Updated body text.'})
        review.refresh_from_db()
        assert review.body == 'Updated body text.'

    def test_owner_can_put_review(self, auth_client, user, facility, review_factory):
        review = review_factory(user=user, facility=facility)
        response = auth_client.put(
            review_update_url(review.pk),
            {
                'facility': facility.pk,
                'rating': 2,
                'body': 'Updated full review.',
                'is_anonymous': False,
                'visit_date': None,
            },
            format='json' 
        )
        print(response.data)
        assert response.status_code == 200

    def test_other_user_cannot_update_review(
        self, api_client, user_factory, facility, review_factory
    ):
        owner = user_factory()
        other = user_factory()
        review = review_factory(user=owner, facility=facility)

        api_client.force_authenticate(user=other)
        response = api_client.patch(review_update_url(review.pk), {'rating': 1})
        assert response.status_code == 403

    def test_unauthenticated_cannot_update(self, api_client, review):
        response = api_client.patch(review_update_url(review.pk), {'rating': 1})
        assert response.status_code == 401

    def test_nonexistent_review_returns_404(self, auth_client):
        response = auth_client.patch(review_update_url(99999), {'rating': 3})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Review Delete  DELETE /api/reviews/<id>/delete/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReviewDelete:

    def test_owner_can_delete_review(self, auth_client, user, facility, review_factory):
        review = review_factory(user=user, facility=facility)
        response = auth_client.delete(review_delete_url(review.pk))
        assert response.status_code == 204

    def test_delete_removes_from_db(self, auth_client, user, facility, review_factory):
        from apps.reviews.models import Review
        review = review_factory(user=user, facility=facility)
        auth_client.delete(review_delete_url(review.pk))
        assert not Review.objects.filter(pk=review.pk).exists()

    def test_other_user_cannot_delete_review(
        self, api_client, user_factory, facility, review_factory
    ):
        owner = user_factory()
        other = user_factory()
        review = review_factory(user=owner, facility=facility)

        api_client.force_authenticate(user=other)
        response = api_client.delete(review_delete_url(review.pk))
        assert response.status_code == 403

    def test_unauthenticated_cannot_delete(self, api_client, review):
        response = api_client.delete(review_delete_url(review.pk))
        assert response.status_code == 401

    def test_nonexistent_review_returns_404(self, auth_client):
        response = auth_client.delete(review_delete_url(99999))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Review Image Upload  POST /api/reviews/<review_id>/images/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReviewImageUpload:

    def test_unauthenticated_cannot_upload(self, api_client, review):
        response = api_client.post(review_images_url(review.pk), {})
        assert response.status_code == 401

    def test_other_user_cannot_upload_to_review(
        self, api_client, user_factory, facility, review_factory
    ):
        owner = user_factory()
        other = user_factory()
        review = review_factory(user=owner, facility=facility)

        api_client.force_authenticate(user=other)
        response = api_client.post(review_images_url(review.pk), {})
        assert response.status_code == 403

    def test_nonexistent_review_returns_404(self, auth_client):
        response = auth_client.post(review_images_url(99999), {})
        assert response.status_code == 404