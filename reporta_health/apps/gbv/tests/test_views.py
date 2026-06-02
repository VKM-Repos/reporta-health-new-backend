"""
Tests for GBV app.

Endpoints under test:
    GET /api/v1/gbv/services/           — list GBV services (public)
    GET /api/v1/gbv/services/nearby/    — nearby GBV services (public)
    GET /api/v1/gbv/nearby/             — combined SARCs + GBV services (public)
"""
import pytest
from django.contrib.gis.geos import Point
from django.core.cache import cache

from apps.gbv.models import GBVService
from apps.facilities.models import Facility

# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

GBV_SERVICE_LIST_URL   = '/api/v1/gbv/services/'
GBV_SERVICE_NEARBY_URL = '/api/v1/gbv/services/nearby/'
GBV_NEARBY_URL         = '/api/v1/gbv/nearby/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_gbv_service(
    name='Test GBV Service',
    state='Lagos',
    lga='Ikeja',
    organisation_type='governmental',
    target_group='adults_and_children',
    lat=6.52,
    lng=3.38,
    is_active=True,
    **kwargs,
):
    return GBVService.objects.create(
        name=name,
        state=state,
        lga=lga,
        organisation_type=organisation_type,
        target_group=target_group,
        address='1 Test Street',
        phone_number='08012345678',
        services='Medical care, counseling',
        operating_hours='Mon-Fri 08:00-16:00',
        location=Point(lng, lat, srid=4326),
        is_active=is_active,
        **kwargs,
    )


def make_sarc_facility(
    name='Test SARC',
    state='Lagos',
    lga='Ikeja',
    lat=6.52,
    lng=3.38,
):
    return Facility.objects.create(
        name=name,
        facility_type='sarcs',
        ownership='private',
        care_level='primary',
        address='1 SARC Street',
        state=state,
        lga=lga,
        location=Point(lng, lat, srid=4326),
        is_active=True,
        has_sarcs=False,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# GBV Service List  GET /api/v1/gbv/services/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGBVServiceList:

    def test_anonymous_can_access(self, api_client):
        r = api_client.get(GBV_SERVICE_LIST_URL)
        assert r.status_code == 200

    def test_returns_paginated_response(self, api_client, db):
        make_gbv_service()
        r = api_client.get(GBV_SERVICE_LIST_URL)
        assert 'count' in r.data
        assert 'results' in r.data

    def test_inactive_excluded(self, api_client, db):
        make_gbv_service(name='Active', is_active=True)
        make_gbv_service(name='Inactive', is_active=False)
        r = api_client.get(GBV_SERVICE_LIST_URL)
        names = [s['name'] for s in r.data['results']]
        assert 'Active' in names
        assert 'Inactive' not in names

    def test_filter_by_state(self, api_client, db):
        make_gbv_service(name='Lagos Service', state='Lagos')
        make_gbv_service(name='Abuja Service', state='FCT')
        r = api_client.get(GBV_SERVICE_LIST_URL, {'state': 'Lagos'})
        names = [s['name'] for s in r.data['results']]
        assert 'Lagos Service' in names
        assert 'Abuja Service' not in names

    def test_filter_by_state_case_insensitive(self, api_client, db):
        make_gbv_service(name='Lagos Service', state='Lagos')
        r = api_client.get(GBV_SERVICE_LIST_URL, {'state': 'lagos'})
        assert r.data['count'] == 1

    def test_filter_by_lga(self, api_client, db):
        make_gbv_service(name='Ikeja Service', lga='Ikeja')
        make_gbv_service(name='Surulere Service', lga='Surulere')
        r = api_client.get(GBV_SERVICE_LIST_URL, {'lga': 'Ikeja'})
        names = [s['name'] for s in r.data['results']]
        assert 'Ikeja Service' in names
        assert 'Surulere Service' not in names

    def test_filter_by_organisation_type(self, api_client, db):
        make_gbv_service(name='Govt Service', organisation_type='governmental')
        make_gbv_service(name='NGO Service', organisation_type='national_ngo')
        r = api_client.get(GBV_SERVICE_LIST_URL, {'organisation_type': 'governmental'})
        names = [s['name'] for s in r.data['results']]
        assert 'Govt Service' in names
        assert 'NGO Service' not in names

    def test_response_fields_present(self, api_client, db):
        make_gbv_service()
        r = api_client.get(GBV_SERVICE_LIST_URL)
        result = r.data['results'][0]
        for field in (
            'id', 'name', 'state', 'lga', 'organisation_type',
            'services', 'target_group', 'address', 'phone_number',
            'contact_person', 'accessibility_info', 'operating_hours',
            'location', 'is_active',
        ):
            assert field in result, f"Missing field: {field}"

    def test_empty_list_returns_200(self, api_client, db):
        r = api_client.get(GBV_SERVICE_LIST_URL)
        assert r.status_code == 200
        assert r.data['count'] == 0


# ---------------------------------------------------------------------------
# GBV Service Nearby  GET /api/v1/gbv/services/nearby/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGBVServiceNearby:

    def test_missing_lat_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lng': '3.38'})
        assert r.status_code == 400
        assert 'error' in r.data

    def test_missing_lng_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52'})
        assert r.status_code == 400

    def test_invalid_lat_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': 'bad', 'lng': '3.38'})
        assert r.status_code == 400

    def test_lat_out_of_range_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '999', 'lng': '3.38'})
        assert r.status_code == 400

    def test_lng_out_of_range_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '999'})
        assert r.status_code == 400

    def test_invalid_radius_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '-5'
        })
        assert r.status_code == 400

    def test_radius_too_large_returns_400(self, api_client):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '9999'
        })
        assert r.status_code == 400

    def test_valid_request_returns_200(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert r.status_code == 200

    def test_returns_paginated_response(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert 'count' in r.data
        assert 'results' in r.data

    def test_radius_restricts_results(self, api_client, db):
        make_gbv_service(name='Near', lat=6.52, lng=3.38)
        make_gbv_service(name='Far', lat=12.0, lng=8.52, state='Kano')
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        names = [s['name'] for s in r.data['results']]
        assert 'Near' in names
        assert 'Far' not in names

    def test_excludes_inactive(self, api_client, db):
        make_gbv_service(name='Active', lat=6.52, lng=3.38, is_active=True)
        make_gbv_service(name='Inactive', lat=6.52, lng=3.38, is_active=False)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        names = [s['name'] for s in r.data['results']]
        assert 'Active' in names
        assert 'Inactive' not in names

    def test_excludes_no_coordinates(self, api_client, db):
        GBVService.objects.create(
            name='No Coords',
            state='Lagos',
            lga='Ikeja',
            organisation_type='governmental',
            location=None,
            is_active=True,
        )
        make_gbv_service(name='Has Coords', lat=6.52, lng=3.38)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        names = [s['name'] for s in r.data['results']]
        assert 'No Coords' not in names
        assert 'Has Coords' in names

    def test_filter_by_state(self, api_client, db):
        make_gbv_service(name='Lagos Near', state='Lagos', lat=6.52, lng=3.38)
        make_gbv_service(name='FCT Near', state='FCT', lat=9.05, lng=7.49)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38',
            'radius_km': '200',
            'state': 'Lagos',
        })
        names = [s['name'] for s in r.data['results']]
        assert 'Lagos Near' in names
        assert 'FCT Near' not in names

    def test_distance_field_present(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert 'distance' in r.data['results'][0]

    def test_anonymous_can_access(self, api_client, db):
        r = api_client.get(GBV_SERVICE_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# GBV Nearby Combined  GET /api/v1/gbv/nearby/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGBVNearby:

    def test_missing_lat_returns_400(self, api_client):
        r = api_client.get(GBV_NEARBY_URL, {'lng': '3.38'})
        assert r.status_code == 400

    def test_missing_lng_returns_400(self, api_client):
        r = api_client.get(GBV_NEARBY_URL, {'lat': '6.52'})
        assert r.status_code == 400

    def test_invalid_lat_returns_400(self, api_client):
        r = api_client.get(GBV_NEARBY_URL, {'lat': 'bad', 'lng': '3.38'})
        assert r.status_code == 400

    def test_lat_out_of_range_returns_400(self, api_client):
        r = api_client.get(GBV_NEARBY_URL, {'lat': '999', 'lng': '3.38'})
        assert r.status_code == 400

    def test_radius_too_large_returns_400(self, api_client):
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '9999'
        })
        assert r.status_code == 400

    def test_valid_request_returns_200(self, api_client, db):
        r = api_client.get(GBV_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert r.status_code == 200

    def test_returns_count_and_results(self, api_client, db):
        r = api_client.get(GBV_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert 'count' in r.data
        assert 'results' in r.data

    def test_gbv_service_included(self, api_client, db):
        make_gbv_service(name='Test GBV', lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        kinds = [item['kind'] for item in r.data['results']]
        assert 'gbv_service' in kinds

    def test_sarc_included(self, api_client, db):
        make_sarc_facility(name='Test SARC', lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        kinds = [item['kind'] for item in r.data['results']]
        assert 'sarc' in kinds

    def test_both_kinds_returned(self, api_client, db):
        make_gbv_service(name='GBV Near', lat=6.52, lng=3.38)
        make_sarc_facility(name='SARC Near', lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        kinds = {item['kind'] for item in r.data['results']}
        assert kinds == {'gbv_service', 'sarc'}

    def test_results_ordered_by_distance(self, api_client, db):
        make_gbv_service(name='Near', lat=6.52, lng=3.38)
        make_gbv_service(name='Far', lat=6.80, lng=3.60)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '100'
        })
        distances = [item['distance_m'] for item in r.data['results']]
        assert distances == sorted(distances)

    def test_result_fields_present(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        result = r.data['results'][0]
        for field in (
            'kind', 'id', 'name', 'state', 'lga',
            'address', 'phone_number', 'services',
            'distance_m', 'location', 'extra',
        ):
            assert field in result, f"Missing field: {field}"

    def test_location_has_lat_lng(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        location = r.data['results'][0]['location']
        assert 'latitude' in location
        assert 'longitude' in location

    def test_gbv_service_extra_fields(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        gbv = next(i for i in r.data['results'] if i['kind'] == 'gbv_service')
        for field in (
            'organisation_type', 'target_group',
            'operating_hours', 'accessibility_info', 'contact_person',
        ):
            assert field in gbv['extra'], f"Missing extra field: {field}"

    def test_sarc_extra_fields(self, api_client, db):
        make_sarc_facility(lat=6.52, lng=3.38)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        sarc = next(i for i in r.data['results'] if i['kind'] == 'sarc')
        for field in (
            'unit_name', 'hotline_number',
            'has_legal_aid', 'has_counseling', 'has_hiv_pep',
        ):
            assert field in sarc['extra'], f"Missing extra field: {field}"

    def test_radius_restricts_results(self, api_client, db):
        make_gbv_service(name='Near', lat=6.52, lng=3.38)
        make_gbv_service(name='Far', lat=12.0, lng=8.52, state='Kano')
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        names = [item['name'] for item in r.data['results']]
        assert 'Near' in names
        assert 'Far' not in names

    def test_inactive_gbv_excluded(self, api_client, db):
        make_gbv_service(name='Inactive GBV', lat=6.52, lng=3.38, is_active=False)
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        names = [item['name'] for item in r.data['results']]
        assert 'Inactive GBV' not in names

    def test_empty_results_when_nothing_nearby(self, api_client, db):
        # Place service far away
        make_gbv_service(name='Far Away', lat=12.0, lng=8.52, state='Kano')
        r = api_client.get(GBV_NEARBY_URL, {
            'lat': '6.52', 'lng': '3.38', 'radius_km': '10'
        })
        assert r.data['count'] == 0
        assert r.data['results'] == []

    def test_anonymous_can_access(self, api_client, db):
        r = api_client.get(GBV_NEARBY_URL, {'lat': '6.52', 'lng': '3.38'})
        assert r.status_code == 200

    def test_cache_returns_same_response(self, api_client, db):
        make_gbv_service(lat=6.52, lng=3.38)
        params = {'lat': '6.52', 'lng': '3.38', 'radius_km': '10'}
        r1 = api_client.get(GBV_NEARBY_URL, params)
        r2 = api_client.get(GBV_NEARBY_URL, params)
        assert r1.data == r2.data