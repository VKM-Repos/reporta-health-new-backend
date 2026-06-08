"""
Tests for report analytics endpoints.

Endpoints under test:
    GET /api/reports/stats/by-reason/          — report counts by reason (admin only)
    GET /api/reports/stats/by-facility-type/   — report counts by facility type (admin only)
    GET /api/reports/stats/by-state/           — report counts by state (admin only)
"""

import pytest
from django.contrib.gis.geos import Point
from apps.facilities.models import Facility
from apps.reports.models import FacilityReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATS_BY_REASON_URL = '/api/v1/reports/stats/by-reason/'
STATS_BY_FACILITY_TYPE_URL = '/api/v1/reports/stats/by-facility-type/'
STATS_BY_STATE_URL = '/api/v1/reports/stats/by-state/'


def _make_facility(state='Lagos', facility_type='hospital'):
    return Facility.objects.create(
        name=f"Test {facility_type} {state}",
        facility_type=facility_type,
        ownership='private',
        care_level='primary',
        address='1 Test St',
        state=state,
        lga='Ikeja',
        location=Point(3.3792, 6.5244, srid=4326),
        is_active=True,
    )


@pytest.fixture
def report_set(db, user_factory):
    u1 = user_factory()
    u2 = user_factory()
    u3 = user_factory()

    lagos_hospital = _make_facility(state='Lagos', facility_type='hospital')
    lagos_clinic = _make_facility(state='Lagos', facility_type='clinic')
    abuja_hospital = _make_facility(state='Abuja', facility_type='hospital')

    FacilityReport.objects.create(
        reporter=u1, facility=lagos_hospital,
        reason='wrong_info', description='Wrong address', status='pending'
    )
    FacilityReport.objects.create(
        reporter=u2, facility=lagos_hospital,
        reason='wrong_info', description='Wrong phone', status='resolved'
    )
    FacilityReport.objects.create(
        reporter=u3, facility=lagos_clinic,
        reason='closed', description='Permanently closed', status='pending'
    )
    FacilityReport.objects.create(
        reporter=u1, facility=abuja_hospital,
        reason='fake', description='Does not exist', status='investigating'
    )


# ---------------------------------------------------------------------------
# Reports by Reason  GET /api/reports/stats/by-reason/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportStatsByReason:

    def test_admin_can_access(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        assert response.status_code == 200

    def test_regular_user_cannot_access(self, auth_client, report_set):
        response = auth_client.get(STATS_BY_REASON_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, api_client, report_set):
        response = api_client.get(STATS_BY_REASON_URL)
        assert response.status_code == 401

    def test_returns_list(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        assert isinstance(response.data, list)

    def test_correct_reason_codes_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        reasons = {r['reason'] for r in response.data}
        assert 'wrong_info' in reasons
        assert 'closed' in reasons
        assert 'fake' in reasons

    def test_reason_label_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        for row in response.data:
            assert 'reason_label' in row

    def test_counts_are_accurate(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        wrong_info = next(r for r in response.data if r['reason'] == 'wrong_info')
        assert wrong_info['count'] == 2

    def test_ordered_by_count_descending(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        counts = [r['count'] for r in response.data]
        assert counts == sorted(counts, reverse=True)

    def test_fields_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_REASON_URL)
        for row in response.data:
            for field in ('reason', 'reason_label', 'count'):
                assert field in row, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Reports by Facility Type  GET /api/reports/stats/by-facility-type/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportStatsByFacilityType:

    def test_admin_can_access(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        assert response.status_code == 200

    def test_regular_user_cannot_access(self, auth_client, report_set):
        response = auth_client.get(STATS_BY_FACILITY_TYPE_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, api_client, report_set):
        response = api_client.get(STATS_BY_FACILITY_TYPE_URL)
        assert response.status_code == 401

    def test_returns_list(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        assert isinstance(response.data, list)

    def test_correct_facility_types_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        types = {r['facility_type'] for r in response.data}
        assert 'hospital' in types
        assert 'clinic' in types

    def test_facility_type_label_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        for row in response.data:
            assert 'facility_type_label' in row

    def test_counts_are_accurate(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        hospital = next(r for r in response.data if r['facility_type'] == 'hospital')
        assert hospital['count'] == 3

    def test_fields_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        for row in response.data:
            for field in ('facility_type', 'facility_type_label', 'count'):
                assert field in row, f"Missing field: {field}"

    def test_ordered_by_count_descending(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_FACILITY_TYPE_URL)
        counts = [r['count'] for r in response.data]
        assert counts == sorted(counts, reverse=True)


# ---------------------------------------------------------------------------
# Reports by State  GET /api/reports/stats/by-state/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportStatsByState:

    def test_admin_can_access(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        assert response.status_code == 200

    def test_regular_user_cannot_access(self, auth_client, report_set):
        response = auth_client.get(STATS_BY_STATE_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, api_client, report_set):
        response = api_client.get(STATS_BY_STATE_URL)
        assert response.status_code == 401

    def test_returns_list(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        assert isinstance(response.data, list)

    def test_correct_states_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        states = {r['state'] for r in response.data}
        assert 'Lagos' in states
        assert 'Abuja' in states

    def test_counts_are_accurate(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        lagos = next(r for r in response.data if r['state'] == 'Lagos')
        assert lagos['count'] == 3

    def test_fields_present(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        for row in response.data:
            for field in ('state', 'count'):
                assert field in row, f"Missing field: {field}"

    def test_ordered_by_count_descending(self, admin_client, report_set):
        response = admin_client.get(STATS_BY_STATE_URL)
        counts = [r['count'] for r in response.data]
        assert counts == sorted(counts, reverse=True)

    def test_empty_state_excluded(self, admin_client, db, user_factory):
        u = user_factory()
        facility = _make_facility(state='', facility_type='hospital')
        FacilityReport.objects.create(
            reporter=u, facility=facility,
            reason='fake', description='No state facility'
        )
        response = admin_client.get(STATS_BY_STATE_URL)
        states = {r['state'] for r in response.data}
        assert '' not in states