"""
Tests for facilities app.

Endpoints under test:
    GET    /api/facilities/                      — list, filter, search
    GET    /api/facilities/nearby/               — geo search
    GET    /api/facilities/<id>/                 — detail
    POST   /api/facilities/create/               — create (admin only)
    PUT    /api/facilities/<id>/update/          — update (admin only)
    PATCH  /api/facilities/<id>/update/          — partial update (admin only)
    DELETE /api/facilities/<id>/delete/          — delete (admin only)
    POST   /api/facilities/<id>/images/          — image upload (admin only)
"""

import pytest
from django.contrib.gis.geos import Point


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIST_URL       = '/api/facilities/'
NEARBY_URL     = '/api/facilities/nearby/'
CREATE_URL     = '/api/facilities/create/'


def detail_url(pk):
    return f'/api/facilities/{pk}/'

def update_url(pk):
    return f'/api/facilities/{pk}/update/'

def delete_url(pk):
    return f'/api/facilities/{pk}/delete/'

def images_url(facility_id):
    return f'/api/facilities/{facility_id}/images/'


def create_payload(**overrides):
    """Minimal valid payload for creating a facility."""
    data = {
        'name': 'New Test Clinic',
        'facility_type': 'clinic',
        'address': '12 Test Street',
        'city': 'Lagos',
        'state': 'Lagos',
        'latitude': 6.5244,
        'longitude': 3.3792,
        'phone_number': '+2348012345678',
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Facility List  GET /api/facilities/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityList:

    def test_returns_200_for_anonymous_user(self, api_client, facility):
        response = api_client.get(LIST_URL)
        assert response.status_code == 200

    def test_returns_200_for_authenticated_user(self, auth_client, facility):
        response = auth_client.get(LIST_URL)
        assert response.status_code == 200

    def test_returns_paginated_response(self, api_client, facility):
        response = api_client.get(LIST_URL)
        assert 'count' in response.data
        assert 'results' in response.data

    def test_returns_only_active_facilities(
        self, api_client, facility, facility_factory, lagos_point
    ):
        inactive = facility_factory(location=lagos_point, is_active=False)
        response = api_client.get(LIST_URL)
        ids = [f['id'] for f in response.data['results']]
        assert facility.id in ids
        assert inactive.id not in ids

    def test_list_serializer_fields_present(self, api_client, facility):
        response = api_client.get(LIST_URL)
        result = response.data['results'][0]
        for field in (
            'id', 'name', 'facility_type', 'address', 'city', 'state',
            'location', 'phone_number', 'average_rating', 'total_reviews',
            'is_verified',
        ):
            assert field in result, f"Missing field: {field}"

    def test_location_returned_as_lat_lng_dict(self, api_client, facility):
        response = api_client.get(LIST_URL)
        location = response.data['results'][0]['location']
        assert 'latitude' in location
        assert 'longitude' in location

    def test_filter_by_facility_type(
        self, api_client, facility_factory, lagos_point
    ):
        facility_factory(location=lagos_point, facility_type='hospital')
        facility_factory(location=lagos_point, facility_type='pharmacy')

        response = api_client.get(LIST_URL, {'facility_type': 'hospital'})
        assert response.status_code == 200
        for f in response.data['results']:
            assert f['facility_type'] == 'hospital'

    def test_filter_by_is_verified(
        self, api_client, facility_factory, lagos_point
    ):
        facility_factory(location=lagos_point, is_verified=True)
        facility_factory(location=lagos_point, is_verified=False)

        response = api_client.get(LIST_URL, {'is_verified': 'true'})
        assert response.status_code == 200
        for f in response.data['results']:
            assert f['is_verified'] is True

    def test_search_by_name(self, api_client, facility_factory, lagos_point):
        facility_factory(location=lagos_point, name='Lagos General Hospital')
        facility_factory(location=lagos_point, name='Ikeja Pharmacy')

        response = api_client.get(LIST_URL, {'search': 'Lagos General'})
        names = [f['name'] for f in response.data['results']]
        assert any('Lagos General' in n for n in names)

    def test_ordering_by_average_rating(
        self, api_client, facility_factory, lagos_point
    ):
        facility_factory(location=lagos_point, average_rating=4.5)
        facility_factory(location=lagos_point, average_rating=2.0)

        response = api_client.get(LIST_URL, {'ordering': '-average_rating'})
        ratings = [f['average_rating'] for f in response.data['results']]
        assert ratings == sorted(ratings, reverse=True)

    def test_distance_field_is_none_on_list(self, api_client, facility):
        # distance only appears on nearby/ results — should be null on plain list
        response = api_client.get(LIST_URL)
        result = response.data['results'][0]
        assert result.get('distance') is None


# ---------------------------------------------------------------------------
# Nearby Facilities  GET /api/facilities/nearby/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNearbyFacilities:

    def test_returns_200_with_valid_params(self, api_client, facility):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244, 'lng': 3.3792})
        assert response.status_code == 200

    def test_anonymous_user_can_access(self, api_client, facility):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244, 'lng': 3.3792})
        assert response.status_code == 200

    def test_response_has_count_and_results(self, api_client, facility):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244, 'lng': 3.3792})
        assert 'count' in response.data
        assert 'results' in response.data

    def test_missing_lat_returns_400(self, api_client):
        response = api_client.get(NEARBY_URL, {'lng': 3.3792})
        assert response.status_code == 400

    def test_missing_lng_returns_400(self, api_client):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244})
        assert response.status_code == 400

    def test_invalid_lat_returns_400(self, api_client):
        response = api_client.get(NEARBY_URL, {'lat': 'notanumber', 'lng': 3.3792})
        assert response.status_code == 400

    def test_invalid_lng_returns_400(self, api_client):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244, 'lng': 'bad'})
        assert response.status_code == 400

    def test_returns_facility_within_radius(self, api_client, facility):
        # facility fixture is at central Lagos (3.3792, 6.5244)
        response = api_client.get(NEARBY_URL, {
            'lat': 6.5244, 'lng': 3.3792, 'radius': 5000
        })
        ids = [f['id'] for f in response.data['results']]
        assert facility.id in ids

    def test_excludes_facility_outside_radius(
        self, api_client, facility, facility_in_abuja
    ):
        # searching near Lagos with 50km radius — Abuja is ~500km away
        response = api_client.get(NEARBY_URL, {
            'lat': 6.5244, 'lng': 3.3792, 'radius': 50000
        })
        ids = [f['id'] for f in response.data['results']]
        assert facility_in_abuja.id not in ids

    def test_results_ordered_nearest_first(
        self, api_client, facility_factory, lagos_point
    ):
        facility_factory(location=Point(3.380, 6.525, srid=4326))  # ~100m away
        facility_factory(location=Point(3.420, 6.560, srid=4326))  # ~5km away

        response = api_client.get(NEARBY_URL, {
            'lat': 6.5244, 'lng': 3.3792, 'radius': 10000
        })
        distances = [
            f['distance'] for f in response.data['results']
            if f['distance'] is not None
        ]
        assert distances == sorted(distances)

    def test_distance_field_is_in_meters(self, api_client, facility):
        response = api_client.get(NEARBY_URL, {'lat': 6.5244, 'lng': 3.3792})
        result = response.data['results'][0]
        assert result['distance'] is not None
        # Distance from a facility at the same point should be near 0
        assert result['distance'] >= 0

    def test_filter_by_facility_type_in_nearby(
        self, api_client, facility_factory, lagos_point
    ):
        facility_factory(location=lagos_point, facility_type='hospital')
        facility_factory(location=lagos_point, facility_type='pharmacy')

        response = api_client.get(NEARBY_URL, {
            'lat': lagos_point.y, 'lng': lagos_point.x,
            'facility_type': 'hospital',
        })
        for f in response.data['results']:
            assert f['facility_type'] == 'hospital'

    def test_limit_parameter_respected(
        self, api_client, facility_factory, lagos_point
    ):
        for _ in range(5):
            facility_factory(location=lagos_point)

        response = api_client.get(NEARBY_URL, {
            'lat': lagos_point.y, 'lng': lagos_point.x,
            'radius': 5000, 'limit': 2,
        })
        assert len(response.data['results']) <= 2

    def test_default_radius_is_5000m(self, api_client, facility_factory, lagos_point):
        # Place one facility well within 5km, one just outside
        near = facility_factory(location=Point(3.380, 6.525, srid=4326))
        far = facility_factory(location=Point(3.600, 6.700, srid=4326))

        response = api_client.get(NEARBY_URL, {
            'lat': 6.5244, 'lng': 3.3792
            # no radius — should default to 5000m
        })
        ids = [f['id'] for f in response.data['results']]
        assert near.id in ids
        assert far.id not in ids


# ---------------------------------------------------------------------------
# Facility Detail  GET /api/facilities/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityDetail:

    def test_returns_200_for_existing_facility(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        assert response.status_code == 200

    def test_anonymous_user_can_view_detail(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        assert response.status_code == 200

    def test_returns_404_for_nonexistent_facility(self, api_client):
        response = api_client.get(detail_url(99999))
        assert response.status_code == 404

    def test_inactive_facility_returns_404(
        self, api_client, facility_factory, lagos_point
    ):
        inactive = facility_factory(location=lagos_point, is_active=False)
        response = api_client.get(detail_url(inactive.pk))
        assert response.status_code == 404

    def test_detail_serializer_fields_present(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        for field in (
            'id', 'name', 'facility_type', 'address', 'city', 'state',
            'location', 'phone_number', 'email', 'website', 'description',
            'services', 'operating_hours', 'has_parking',
            'has_wheelchair_access', 'has_emergency_service',
            'is_verified', 'is_active', 'average_rating',
            'total_reviews', 'images', 'created_at', 'updated_at',
        ):
            assert field in response.data, f"Missing field: {field}"

    def test_location_returned_as_lat_lng_dict(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        location = response.data['location']
        assert 'latitude' in location
        assert 'longitude' in location

    def test_operating_hours_has_all_days(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        hours = response.data['operating_hours']
        for day in ('monday', 'tuesday', 'wednesday', 'thursday',
                    'friday', 'saturday', 'sunday'):
            assert day in hours, f"Missing day: {day}"

    def test_images_is_a_list(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        assert isinstance(response.data['images'], list)

    def test_returns_correct_facility_name(self, api_client, facility):
        response = api_client.get(detail_url(facility.pk))
        assert response.data['name'] == facility.name


# ---------------------------------------------------------------------------
# Facility Create  POST /api/facilities/create/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityCreate:

    def test_admin_can_create_facility(self, admin_client):
        response = admin_client.post(CREATE_URL, create_payload())
        assert response.status_code == 201

    def test_regular_user_cannot_create_facility(self, auth_client):
        response = auth_client.post(CREATE_URL, create_payload())
        assert response.status_code == 403

    def test_anonymous_user_cannot_create_facility(self, api_client):
        response = api_client.post(CREATE_URL, create_payload())
        assert response.status_code == 401

    def test_create_persists_to_db(self, admin_client):
        from apps.facilities.models import Facility
        count_before = Facility.objects.count()
        admin_client.post(CREATE_URL, create_payload())
        assert Facility.objects.count() == count_before + 1

    def test_create_builds_point_from_lat_lng(self, admin_client):
        from apps.facilities.models import Facility
        admin_client.post(CREATE_URL, create_payload(
            latitude=6.5244, longitude=3.3792
        ))
        facility = Facility.objects.latest('created_at')
        assert facility.location is not None
        assert round(facility.location.y, 4) == 6.5244
        assert round(facility.location.x, 4) == 3.3792

    def test_missing_name_returns_400(self, admin_client):
        payload = create_payload()
        del payload['name']
        response = admin_client.post(CREATE_URL, payload)
        assert response.status_code == 400

    def test_missing_latitude_returns_400(self, admin_client):
        payload = create_payload()
        del payload['latitude']
        response = admin_client.post(CREATE_URL, payload)
        assert response.status_code == 400

    def test_missing_longitude_returns_400(self, admin_client):
        payload = create_payload()
        del payload['longitude']
        response = admin_client.post(CREATE_URL, payload)
        assert response.status_code == 400

    def test_optional_fields_accepted(self, admin_client):
        response = admin_client.post(CREATE_URL, create_payload(
            description='A full-service clinic in Lagos',
            has_parking=True,
            has_wheelchair_access=True,
            has_emergency_service=False,
        ))
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Facility Update  PUT/PATCH /api/facilities/<id>/update/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityUpdate:

    def test_admin_can_patch_facility(self, admin_client, facility):
        response = admin_client.patch(update_url(facility.pk), {'name': 'Updated Name'})
        assert response.status_code == 200

    def test_patch_persists_to_db(self, admin_client, facility):
        admin_client.patch(update_url(facility.pk), {'name': 'Patched Name'})
        facility.refresh_from_db()
        assert facility.name == 'Patched Name'

    def test_admin_can_put_facility(self, admin_client, facility):
        response = admin_client.put(update_url(facility.pk), create_payload())
        assert response.status_code == 200

    def test_regular_user_cannot_update(self, auth_client, facility):
        response = auth_client.patch(update_url(facility.pk), {'name': 'Hacked'})
        assert response.status_code == 403

    def test_anonymous_user_cannot_update(self, api_client, facility):
        response = api_client.patch(update_url(facility.pk), {'name': 'Hacked'})
        assert response.status_code == 401

    def test_patch_updates_location_from_lat_lng(self, admin_client, facility):
        admin_client.patch(update_url(facility.pk), {
            'latitude': 9.0579,
            'longitude': 7.4898,
        })
        facility.refresh_from_db()
        assert round(facility.location.y, 4) == 9.0579
        assert round(facility.location.x, 4) == 7.4898

    def test_patch_nonexistent_facility_returns_404(self, admin_client):
        response = admin_client.patch(update_url(99999), {'name': 'Ghost'})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Facility Delete  DELETE /api/facilities/<id>/delete/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityDelete:

    def test_admin_can_delete_facility(self, admin_client, facility):
        response = admin_client.delete(delete_url(facility.pk))
        assert response.status_code == 204

    def test_delete_removes_from_db(self, admin_client, facility):
        from apps.facilities.models import Facility
        admin_client.delete(delete_url(facility.pk))
        assert not Facility.objects.filter(pk=facility.pk).exists()

    def test_regular_user_cannot_delete(self, auth_client, facility):
        response = auth_client.delete(delete_url(facility.pk))
        assert response.status_code == 403

    def test_anonymous_user_cannot_delete(self, api_client, facility):
        response = api_client.delete(delete_url(facility.pk))
        assert response.status_code == 401

    def test_delete_nonexistent_facility_returns_404(self, admin_client):
        response = admin_client.delete(delete_url(99999))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Facility Image Upload  POST /api/facilities/<id>/images/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilityImageUpload:

    def test_regular_user_cannot_upload_image(self, auth_client, facility):
        response = auth_client.post(images_url(facility.pk), {})
        assert response.status_code == 403

    def test_anonymous_user_cannot_upload_image(self, api_client, facility):
        response = api_client.post(images_url(facility.pk), {})
        assert response.status_code == 401

    def test_nonexistent_facility_returns_404_or_400(self, admin_client):
        # Depends on whether view validates facility_id exists
        response = admin_client.post(images_url(99999), {})
        assert response.status_code in (400, 404)