"""
Tests for SARC endpoints.

Endpoints under test:
    GET /api/facilities/sarcs/          — list SARC facilities (public)
    GET /api/facilities/sarcs/<int:pk>/ — SARC facility detail (public)
"""

import pytest
from django.contrib.gis.geos import Point
from apps.facilities.models import Facility, SARCProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SARC_LIST_URL = '/api/facilities/sarcs/'


def sarc_detail_url(pk):
    return f'/api/facilities/sarcs/{pk}/'


def make_facility(name='Test SARC', facility_type='sarcs', has_sarcs=False, state='Lagos', is_active=True):
    return Facility.objects.create(
        name=name,
        facility_type=facility_type,
        ownership='private',
        care_level='primary',
        address='1 Test Street',
        state=state,
        lga='Ikeja',
        location=Point(3.3792, 6.5244, srid=4326),
        is_active=is_active,
        has_sarcs=has_sarcs,
    )


def make_sarc_profile(facility, **kwargs):
    defaults = {
        'unit_name': 'Hope Centre',
        'hotline_number': '08012345678',
        'is_24_hours': True,
        'accepts_walk_ins': True,
        'confidentiality_assured': True,
        'has_legal_aid': True,
        'has_counseling': True,
        'has_hiv_pep': True,
        'has_police_presence': False,
        'has_emergency_contraception': True,
        'has_shelter_referral': False,
        'has_forensic': True,
        'has_sti_testing': True,
        'has_court_support': False,
    }
    defaults.update(kwargs)
    return SARCProfile.objects.create(facility=facility, **defaults)


@pytest.fixture
def standalone_sarc(db):
    """A standalone SARC facility."""
    f = make_facility(name='Mirabel Centre', facility_type='sarcs')
    make_sarc_profile(f)
    return f


@pytest.fixture
def hospital_with_sarc(db):
    """A hospital that has a SARC unit."""
    f = make_facility(name='Lagos Island General Hospital', facility_type='hospital', has_sarcs=True)
    make_sarc_profile(f, unit_name='Gender Violence Unit')
    return f


@pytest.fixture
def regular_hospital(db):
    """A hospital with no SARC — should not appear in SARC results."""
    return make_facility(name='Regular Hospital', facility_type='hospital', has_sarcs=False)


@pytest.fixture
def inactive_sarc(db):
    """An inactive SARC — should not appear in results."""
    return make_facility(name='Inactive SARC', facility_type='sarcs', is_active=False)


@pytest.fixture
def abuja_sarc(db):
    """A SARC in Abuja for state filter tests."""
    f = Facility.objects.create(
        name='Abuja SARC',
        facility_type='sarcs',
        ownership='government',
        care_level='secondary',
        address='1 Abuja Road',
        state='Abuja',
        lga='Municipal',
        location=Point(7.4898, 9.0579, srid=4326),
        is_active=True,
    )
    make_sarc_profile(f, has_police_presence=True, has_legal_aid=False)
    return f


# ---------------------------------------------------------------------------
# SARC List  GET /api/facilities/sarcs/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSARCList:

    def test_anonymous_can_access(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        assert response.status_code == 200

    def test_authenticated_can_access(self, auth_client, standalone_sarc):
        response = auth_client.get(SARC_LIST_URL)
        assert response.status_code == 200

    def test_returns_paginated_response(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        assert 'count' in response.data
        assert 'results' in response.data

    def test_standalone_sarc_included(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        ids = [r['id'] for r in response.data['results']]
        assert standalone_sarc.pk in ids

    def test_hospital_with_sarc_included(self, api_client, hospital_with_sarc):
        response = api_client.get(SARC_LIST_URL)
        ids = [r['id'] for r in response.data['results']]
        assert hospital_with_sarc.pk in ids

    def test_regular_hospital_excluded(self, api_client, regular_hospital, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        ids = [r['id'] for r in response.data['results']]
        assert regular_hospital.pk not in ids

    def test_inactive_sarc_excluded(self, api_client, inactive_sarc, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        ids = [r['id'] for r in response.data['results']]
        assert inactive_sarc.pk not in ids

    def test_response_fields_present(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        result = response.data['results'][0]
        for field in ('id', 'name', 'facility_type', 'has_sarcs', 'sarc_profile', 'is_standalone_sarc'):
            assert field in result, f"Missing field: {field}"

    def test_sarc_profile_nested(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        result = response.data['results'][0]
        assert isinstance(result['sarc_profile'], dict)

    def test_is_standalone_sarc_true_for_sarcs_type(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL)
        result = next(r for r in response.data['results'] if r['id'] == standalone_sarc.pk)
        assert result['is_standalone_sarc'] is True

    def test_is_standalone_sarc_false_for_hospital(self, api_client, hospital_with_sarc):
        response = api_client.get(SARC_LIST_URL)
        result = next(r for r in response.data['results'] if r['id'] == hospital_with_sarc.pk)
        assert result['is_standalone_sarc'] is False

    def test_filter_by_state(self, api_client, standalone_sarc, abuja_sarc):
        response = api_client.get(SARC_LIST_URL, {'state': 'Lagos'})
        ids = [r['id'] for r in response.data['results']]
        assert standalone_sarc.pk in ids
        assert abuja_sarc.pk not in ids

    def test_filter_by_state_case_insensitive(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL, {'state': 'lagos'})
        assert response.status_code == 200
        ids = [r['id'] for r in response.data['results']]
        assert standalone_sarc.pk in ids

    def test_filter_by_valid_service(self, api_client, standalone_sarc, abuja_sarc):
        # standalone_sarc has legal_aid=True, abuja_sarc has legal_aid=False
        response = api_client.get(SARC_LIST_URL, {'service': 'legal_aid'})
        assert response.status_code == 200
        ids = [r['id'] for r in response.data['results']]
        assert standalone_sarc.pk in ids
        assert abuja_sarc.pk not in ids

    def test_filter_by_invalid_service_returns_400(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL, {'service': 'not_a_service'})
        assert response.status_code == 400
        assert 'valid_services' in response.data

    def test_nearby_search_returns_results(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL, {
            'lat': 6.5244, 'lng': 3.3792, 'radius': 50000
        })
        assert response.status_code == 200

    def test_nearby_search_invalid_coords_returns_400(self, api_client, standalone_sarc):
        response = api_client.get(SARC_LIST_URL, {'lat': 'invalid', 'lng': 'coords'})
        assert response.status_code == 400

    def test_nearby_radius_capped_at_50km(self, api_client, standalone_sarc):
        # Should not error even with huge radius — gets capped
        response = api_client.get(SARC_LIST_URL, {
            'lat': 6.5244, 'lng': 3.3792, 'radius': 999999
        })
        assert response.status_code == 200

    def test_empty_list_when_no_sarcs(self, api_client):
        response = api_client.get(SARC_LIST_URL)
        assert response.status_code == 200
        assert response.data['count'] == 0


# ---------------------------------------------------------------------------
# SARC Detail  GET /api/facilities/sarcs/<int:pk>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSARCDetail:

    def test_anonymous_can_access(self, api_client, standalone_sarc):
        response = api_client.get(sarc_detail_url(standalone_sarc.pk))
        assert response.status_code == 200

    def test_returns_correct_facility(self, api_client, standalone_sarc):
        response = api_client.get(sarc_detail_url(standalone_sarc.pk))
        assert response.data['id'] == standalone_sarc.pk

    def test_nonexistent_sarc_returns_404(self, api_client):
        response = api_client.get(sarc_detail_url(99999))
        assert response.status_code == 404

    def test_regular_hospital_returns_404(self, api_client, regular_hospital):
        # Regular hospital without SARC should not be accessible via SARC endpoint
        response = api_client.get(sarc_detail_url(regular_hospital.pk))
        assert response.status_code == 404

    def test_inactive_sarc_returns_404(self, api_client, inactive_sarc):
        response = api_client.get(sarc_detail_url(inactive_sarc.pk))
        assert response.status_code == 404

    def test_detail_fields_present(self, api_client, standalone_sarc):
        response = api_client.get(sarc_detail_url(standalone_sarc.pk))
        for field in ('id', 'name', 'facility_type', 'has_sarcs', 'sarc_profile', 'is_standalone_sarc'):
            assert field in response.data, f"Missing field: {field}"

    def test_sarc_profile_fields_present(self, api_client, standalone_sarc):
        response = api_client.get(sarc_detail_url(standalone_sarc.pk))
        profile = response.data['sarc_profile']
        for field in (
            'unit_name', 'hotline_number', 'is_24_hours', 'accepts_walk_ins',
            'confidentiality_assured', 'has_legal_aid', 'has_counseling',
            'has_hiv_pep', 'has_police_presence', 'has_emergency_contraception',
            'has_shelter_referral', 'has_forensic', 'has_sti_testing', 'has_court_support',
            'languages', 'additional_info',
        ):
            assert field in profile, f"Missing SARC profile field: {field}"

    def test_hospital_with_sarc_accessible(self, api_client, hospital_with_sarc):
        response = api_client.get(sarc_detail_url(hospital_with_sarc.pk))
        assert response.status_code == 200

    def test_unit_name_correct(self, api_client, standalone_sarc):
        response = api_client.get(sarc_detail_url(standalone_sarc.pk))
        assert response.data['sarc_profile']['unit_name'] == 'Hope Centre'