"""
Global pytest fixtures and configuration for Reporta Health
"""

import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient


from apps.factories import (
    FacilityFactory,
    ReportFactory,
    ReviewFactory,
    UserFactory,
)


@pytest.fixture
def user_factory(db):
    """Factory for users.User — call with keyword overrides."""
    return UserFactory


@pytest.fixture
def facility_factory(db):
    """Factory for facilities.Facility — call with keyword overrides."""
    return FacilityFactory


@pytest.fixture
def review_factory(db):
    """Factory for reviews.Review — call with keyword overrides."""
    return ReviewFactory


@pytest.fixture
def report_factory(db):
    """Factory for reports.Report — call with keyword overrides."""
    return ReportFactory
# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated DRF test client — regular user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Authenticated DRF test client — staff/admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db, user_factory):
    """A standard verified user."""
    return user_factory(is_verified=True)


@pytest.fixture
def admin_user(db, user_factory):
    """A staff user with admin access."""
    return user_factory(is_staff=True, is_superuser=True, is_verified=True)


@pytest.fixture
def unverified_user(db, user_factory):
    """A user who hasn't verified their email."""
    return user_factory(is_verified=False)


# ---------------------------------------------------------------------------
# Locations — reusable geo coordinates (Nigeria)
# ---------------------------------------------------------------------------

@pytest.fixture
def lagos_point():
    """Central Lagos coordinates."""
    return Point(3.3792, 6.5244, srid=4326)  # lng, lat


@pytest.fixture
def abuja_point():
    """Central Abuja coordinates."""
    return Point(7.4898, 9.0579, srid=4326)


@pytest.fixture
def nearby_point(lagos_point):
    """A point ~1km from central Lagos — useful for distance tests."""
    return Point(lagos_point.x + 0.009, lagos_point.y + 0.009, srid=4326)


@pytest.fixture
def far_point():
    """Cape Town — far from Lagos, useful for 'not in range' tests."""
    return Point(18.4241, -33.9249, srid=4326)


# ---------------------------------------------------------------------------
# Facilities
# ---------------------------------------------------------------------------

@pytest.fixture
def facility(db, facility_factory, lagos_point):
    """A single verified facility in Lagos."""
    return facility_factory(location=lagos_point, is_verified=True)


@pytest.fixture
def unverified_facility(db, facility_factory, lagos_point):
    return facility_factory(location=lagos_point, is_verified=False)


@pytest.fixture
def facility_in_abuja(db, facility_factory, abuja_point):
    return facility_factory(location=abuja_point, is_verified=True)


@pytest.fixture
def multiple_facilities(db, facility_factory, lagos_point):
    """5 facilities at different distances from central Lagos."""
    offsets = [0.001, 0.005, 0.01, 0.05, 0.5]
    return [
        facility_factory(
            location=Point(lagos_point.x + o, lagos_point.y + o, srid=4326),
            is_verified=True,
        )
        for o in offsets
    ]


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@pytest.fixture
def review(db, review_factory, user, facility):
    """A single published review."""
    return review_factory(user=user, facility=facility)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@pytest.fixture
def report(db, report_factory, user, facility):
    return report_factory(reporter=user, facility=facility)


# @pytest.fixture
# def anonymous_report(db, report_factory, facility):
#     """A report submitted without a user."""
#     return report_factory(user=None, facility=facility)