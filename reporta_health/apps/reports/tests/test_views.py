"""
Tests for reports app.

Endpoints under test:
    POST   /api/reports/create/                — submit a report (auth)
    GET    /api/reports/                       — list all reports (admin only)
    GET    /api/reports/my-reports/            — list current user's reports (auth)
    GET    /api/reports/<id>/                  — report detail (admin only)
    PATCH  /api/reports/<id>/status/           — update report status (admin only)
    POST   /api/reports/<report_id>/images/    — upload evidence image (auth, owner only)
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPORT_LIST_URL = '/api/reports/'
REPORT_CREATE_URL = '/api/reports/create/'
MY_REPORTS_URL = '/api/reports/my-reports/'


def report_detail_url(pk):
    return f'/api/reports/{pk}/'


def report_status_url(pk):
    return f'/api/reports/{pk}/status/'


def report_images_url(report_id):
    return f'/api/reports/{report_id}/images/'


def create_report_payload(**overrides):
    data = {
        'reason': 'wrong_info',
        'description': 'The facility information displayed is incorrect.',
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Report Create  POST /api/reports/create/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportCreate:

    def test_authenticated_user_can_create_report(self, auth_client, facility):
        payload = create_report_payload(facility=facility.pk)
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 201

    def test_unauthenticated_user_cannot_create_report(self, api_client, facility):
        payload = create_report_payload(facility=facility.pk)
        response = api_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 401

    def test_reporter_set_from_request_user(self, auth_client, user, facility):
        auth_client.post(REPORT_CREATE_URL, create_report_payload(facility=facility.pk))
        from apps.reports.models import FacilityReport
        report = FacilityReport.objects.filter(facility=facility).first()
        assert report.reporter == user

    def test_create_persists_to_db(self, auth_client, facility):
        from apps.reports.models import FacilityReport
        count_before = FacilityReport.objects.count()
        auth_client.post(REPORT_CREATE_URL, create_report_payload(facility=facility.pk))
        assert FacilityReport.objects.count() == count_before + 1

    def test_default_status_is_pending(self, auth_client, facility):
        auth_client.post(REPORT_CREATE_URL, create_report_payload(facility=facility.pk))
        from apps.reports.models import FacilityReport
        report = FacilityReport.objects.filter(facility=facility).first()
        assert report.status == 'pending'

    def test_response_contains_expected_fields(self, auth_client, facility):
        response = auth_client.post(
            REPORT_CREATE_URL, create_report_payload(facility=facility.pk)
        )
        for field in ('facility', 'reason', 'description'):
            assert field in response.data, f"Missing field: {field}"

    def test_missing_reason_returns_400(self, auth_client, facility):
        payload = create_report_payload(facility=facility.pk)
        del payload['reason']
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 400

    def test_missing_description_returns_400(self, auth_client, facility):
        payload = create_report_payload(facility=facility.pk)
        del payload['description']
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 400

    def test_missing_facility_returns_400(self, auth_client):
        payload = create_report_payload()
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 400

    def test_invalid_reason_returns_400(self, auth_client, facility):
        payload = create_report_payload(facility=facility.pk, reason='not_a_valid_reason')
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 400

    def test_nonexistent_facility_returns_400(self, auth_client):
        payload = create_report_payload(facility=99999)
        response = auth_client.post(REPORT_CREATE_URL, payload)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Report List  GET /api/reports/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportList:

    def test_admin_can_list_reports(self, admin_client):
        response = admin_client.get(REPORT_LIST_URL)
        assert response.status_code == 200

    def test_regular_user_cannot_list_reports(self, auth_client):
        response = auth_client.get(REPORT_LIST_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_reports(self, api_client):
        response = api_client.get(REPORT_LIST_URL)
        assert response.status_code == 401

    def test_returns_paginated_response(self, admin_client):
        response = admin_client.get(REPORT_LIST_URL)
        assert 'count' in response.data
        assert 'results' in response.data

    def test_report_fields_present(self, admin_client, report):
        response = admin_client.get(REPORT_LIST_URL)
        result = response.data['results'][0]
        for field in (
            'id', 'facility', 'facility_name', 'reporter', 'reason',
            'reason_display', 'description', 'status', 'status_display',
            'admin_notes', 'images', 'created_at', 'updated_at', 'resolved_at',
        ):
            assert field in result, f"Missing field: {field}"

    def test_filter_by_status(self, admin_client, user_factory, facility, report_factory):
        u1 = user_factory()
        u2 = user_factory()
        report_factory(reporter=u1, facility=facility, status='pending')
        report_factory(reporter=u2, facility=facility, status='resolved')

        response = admin_client.get(REPORT_LIST_URL, {'status': 'pending'})
        for r in response.data['results']:
            assert r['status'] == 'pending'

    def test_filter_by_facility(self, admin_client, facility_factory, user, report_factory, lagos_point):
        other_facility = facility_factory(location=lagos_point)
        report_factory(reporter=user, facility=facility_factory(location=lagos_point))
        report_factory(reporter=user, facility=other_facility)

        response = admin_client.get(REPORT_LIST_URL, {'facility': other_facility.pk})
        assert all(r['facility'] == other_facility.pk for r in response.data['results'])

    def test_ordering_by_created_at(self, admin_client, user_factory, facility, report_factory):
        u1 = user_factory()
        u2 = user_factory()
        report_factory(reporter=u1, facility=facility)
        report_factory(reporter=u2, facility=facility)
        response = admin_client.get(REPORT_LIST_URL, {'ordering': '-created_at'})
        assert response.status_code == 200

    def test_reporter_is_nested_object(self, admin_client, report):
        response = admin_client.get(REPORT_LIST_URL)
        result = response.data['results'][0]
        assert isinstance(result['reporter'], dict)


# ---------------------------------------------------------------------------
# My Reports  GET /api/reports/my-reports/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMyReports:

    def test_authenticated_user_can_list_own_reports(self, auth_client):
        response = auth_client.get(MY_REPORTS_URL)
        assert response.status_code == 200

    def test_unauthenticated_cannot_access_my_reports(self, api_client):
        response = api_client.get(MY_REPORTS_URL)
        assert response.status_code == 401

    def test_returns_only_current_user_reports(
        self, auth_client, user, user_factory, facility, report_factory
    ):
        other = user_factory()
        report_factory(reporter=user, facility=facility)
        report_factory(reporter=user, facility=facility)
        report_factory(reporter=other, facility=facility)

        response = auth_client.get(MY_REPORTS_URL)
        assert response.data['count'] == 2

    def test_returns_empty_when_no_reports(self, auth_client):
        response = auth_client.get(MY_REPORTS_URL)
        assert response.data['count'] == 0

    def test_report_fields_present(self, auth_client, user, facility, report_factory):
        report_factory(reporter=user, facility=facility)
        response = auth_client.get(MY_REPORTS_URL)
        result = response.data['results'][0]
        for field in (
            'id', 'facility', 'facility_name', 'reporter', 'reason',
            'description', 'status', 'images', 'created_at',
        ):
            assert field in result, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Report Detail  GET /api/reports/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportDetail:

    def test_admin_can_view_report_detail(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        assert response.status_code == 200

    def test_regular_user_cannot_view_detail(self, auth_client, report):
        response = auth_client.get(report_detail_url(report.pk))
        assert response.status_code == 403

    def test_unauthenticated_cannot_view_detail(self, api_client, report):
        response = api_client.get(report_detail_url(report.pk))
        assert response.status_code == 401

    def test_returns_correct_report(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        assert response.data['id'] == report.pk

    def test_nonexistent_report_returns_404(self, admin_client):
        response = admin_client.get(report_detail_url(99999))
        assert response.status_code == 404

    def test_detail_fields_present(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        for field in (
            'id', 'facility', 'facility_name', 'reporter', 'reason',
            'reason_display', 'description', 'status', 'status_display',
            'admin_notes', 'images', 'created_at', 'updated_at', 'resolved_at',
        ):
            assert field in response.data, f"Missing field: {field}"

    def test_images_is_a_list(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        assert isinstance(response.data['images'], list)

    def test_reporter_is_nested_object(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        assert isinstance(response.data['reporter'], dict)

    def test_facility_name_matches(self, admin_client, report):
        response = admin_client.get(report_detail_url(report.pk))
        assert response.data['facility_name'] == report.facility.name


# ---------------------------------------------------------------------------
# Report Status Update  PATCH /api/reports/<id>/status/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportStatusUpdate:

    def test_admin_can_update_status(self, admin_client, report):
        response = admin_client.patch(
            report_status_url(report.pk), {'status': 'investigating'}
        )
        assert response.status_code == 200

    def test_status_persists_to_db(self, admin_client, report):
        admin_client.patch(report_status_url(report.pk), {'status': 'resolved'})
        report.refresh_from_db()
        assert report.status == 'resolved'

    def test_admin_notes_can_be_set(self, admin_client, report):
        admin_client.patch(
            report_status_url(report.pk),
            {'status': 'rejected', 'admin_notes': 'Duplicate report.'}
        )
        report.refresh_from_db()
        assert report.admin_notes == 'Duplicate report.'

    def test_resolved_at_set_when_status_is_resolved(self, admin_client, report):
        admin_client.patch(report_status_url(report.pk), {'status': 'resolved'})
        report.refresh_from_db()
        assert report.resolved_at is not None

    def test_resolved_at_not_set_for_other_statuses(self, admin_client, report):
        admin_client.patch(report_status_url(report.pk), {'status': 'investigating'})
        report.refresh_from_db()
        assert report.resolved_at is None

    def test_response_contains_full_report_data(self, admin_client, report):
        response = admin_client.patch(
            report_status_url(report.pk), {'status': 'investigating'}
        )
        for field in ('id', 'status', 'facility', 'reporter', 'description'):
            assert field in response.data, f"Missing field: {field}"

    def test_regular_user_cannot_update_status(self, auth_client, report):
        response = auth_client.patch(
            report_status_url(report.pk), {'status': 'resolved'}
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_update_status(self, api_client, report):
        response = api_client.patch(
            report_status_url(report.pk), {'status': 'resolved'}
        )
        assert response.status_code == 401

    def test_invalid_status_returns_400(self, admin_client, report):
        response = admin_client.patch(
            report_status_url(report.pk), {'status': 'not_a_valid_status'}
        )
        assert response.status_code == 400

    def test_nonexistent_report_returns_404(self, admin_client):
        response = admin_client.patch(report_status_url(99999), {'status': 'resolved'})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Report Image Upload  POST /api/reports/<report_id>/images/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReportImageUpload:

    def test_unauthenticated_cannot_upload(self, api_client, report):
        response = api_client.post(report_images_url(report.pk), {})
        assert response.status_code == 401

    def test_other_user_cannot_upload_to_report(
        self, api_client, user_factory, facility, report_factory
    ):
        owner = user_factory()
        other = user_factory()
        report = report_factory(reporter=owner, facility=facility)

        api_client.force_authenticate(user=other)
        response = api_client.post(report_images_url(report.pk), {})
        assert response.status_code == 403

    def test_nonexistent_report_returns_404(self, auth_client):
        response = auth_client.post(report_images_url(99999), {})
        assert response.status_code == 404