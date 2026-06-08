"""
Tests for analytics/statistics endpoints.
"""
import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from apps.facilities.models import Facility


# ── fixtures ──────────────────────────────────────────────────────────────────

def _make_facility(**kwargs) -> Facility:
    defaults = dict(
        name="Test Facility",
        facility_type="hospital",
        ownership="private",
        care_level="primary",
        address="1 Test St",
        state="Lagos",
        lga="Ikeja",
        location=Point(3.3792, 6.5244, srid=4326),
        is_active=True,
    )
    defaults.update(kwargs)
    return Facility.objects.create(**defaults)


@pytest.fixture
def facility_set(db):
    """
    10 facilities across 2 states / 3 LGAs / 2 types / 2 ownership /
    2 care levels so every analytic dimension is exercised.
    """
    objs = [
        # Lagos / Ikeja — hospitals
        _make_facility(name="F1", facility_type="hospital",  ownership="private",          care_level="primary",   state="Lagos", lga="Ikeja"),
        _make_facility(name="F2", facility_type="hospital",  ownership="private",          care_level="secondary", state="Lagos", lga="Ikeja"),
        _make_facility(name="F3", facility_type="hospital",  ownership="federal_government", care_level="tertiary", state="Lagos", lga="Ikeja"),
        # Lagos / Eti-Osa — clinics
        _make_facility(name="F4", facility_type="clinic",    ownership="private",          care_level="primary",   state="Lagos", lga="Eti-Osa"),
        _make_facility(name="F5", facility_type="clinic",    ownership="mission",          care_level="primary",   state="Lagos", lga="Eti-Osa"),
        # Lagos / Ikeja — pharmacy
        _make_facility(name="F6", facility_type="pharmacy",  ownership="private",          care_level="primary",   state="Lagos", lga="Ikeja"),
        # Abuja / AMAC
        _make_facility(name="F7", facility_type="hospital",  ownership="state_government", care_level="secondary", state="Abuja", lga="AMAC"),
        _make_facility(name="F8", facility_type="clinic",    ownership="private",          care_level="primary",   state="Abuja", lga="AMAC"),
        _make_facility(name="F9", facility_type="laboratory", ownership="private",         care_level="primary",   state="Abuja", lga="AMAC"),
        # inactive — must be excluded from all stats
        _make_facility(name="F10", is_active=False, state="Lagos", lga="Ikeja"),
    ]
    return objs


# ── all-states ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFacilityStatsByAllStates:
    url = "/api/v1/facilities/stats/by-state/"

    def test_returns_200(self, client, facility_set):
        r = client.get(self.url)
        assert r.status_code == 200

    def test_correct_state_count(self, client, facility_set):
        r = client.get(self.url)
        states = [row["state"] for row in r.json()]
        assert set(states) == {"Lagos", "Abuja"}

    def test_inactive_excluded(self, client, facility_set):
        r = client.get(self.url)
        lagos = next(row for row in r.json() if row["state"] == "Lagos")
        # F10 is inactive; Lagos active = F1..F6 = 6
        assert lagos["total"] == 6

    def test_breakdown_sums_to_total(self, client, facility_set):
        r = client.get(self.url)
        for row in r.json():
            assert sum(b["count"] for b in row["breakdown"]) == row["total"]

    def test_cached_response(self, client, facility_set):
        r1 = client.get(self.url)
        r2 = client.get(self.url)
        assert r1.json() == r2.json()


# ── single state ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFacilityStatsByState:
    def url(self, state):
        return f"/api/v1/facilities/stats/by-state/{state}/"
    
    def test_returns_200_for_known_state(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        assert r.status_code == 200

    def test_returns_404_for_unknown_state(self, client, facility_set):
        r = client.get(self.url("Narnia"))
        assert r.status_code == 404

    def test_case_insensitive_lookup(self, client, facility_set):
        r = client.get(self.url("lagos"))
        assert r.status_code == 200
        assert r.json()["state"] == "Lagos"

    def test_correct_total(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        assert r.json()["total"] == 6  # F1..F6

    def test_breakdown_has_facility_type_label(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        types = {b["facility_type"] for b in r.json()["breakdown"]}
        assert "hospital" in types
        assert "clinic" in types

    def test_inactive_excluded(self, client, facility_set):
        """F10 is inactive; ensure it doesn't appear in totals."""
        r = client.get(self.url("Lagos"))
        assert r.json()["total"] == 6


# ── state ownership ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFacilityStatsByStateOwnership:
    def url(self, state):
        return f"/api/v1/facilities/stats/by-state/{state}/ownership/"

    def test_returns_200(self, client, facility_set):
        assert client.get(self.url("Lagos")).status_code == 200

    def test_returns_404_for_unknown_state(self, client, facility_set):
        assert client.get(self.url("Unknown")).status_code == 404

    def test_breakdown_contains_ownership_label(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        labels = {b["ownership_label"] for b in r.json()["breakdown"]}
        assert "Private" in labels

    def test_breakdown_sums_to_total(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        data = r.json()
        assert sum(b["count"] for b in data["breakdown"]) == data["total"]

    def test_federal_government_present(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        ownerships = {b["ownership"] for b in r.json()["breakdown"]}
        assert "federal_government" in ownerships


# ── state care level ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFacilityStatsByStateCareLevel:
    def url(self, state):
        return f"/api/v1/facilities/stats/by-state/{state}/care-level/"

    def test_returns_200(self, client, facility_set):
        assert client.get(self.url("Lagos")).status_code == 200

    def test_returns_404_for_unknown_state(self, client, facility_set):
        assert client.get(self.url("Unknown")).status_code == 404

    def test_breakdown_sums_to_total(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        data = r.json()
        assert sum(b["count"] for b in data["breakdown"]) == data["total"]

    def test_care_level_label_present(self, client, facility_set):
        r = client.get(self.url("Lagos"))
        labels = {b["care_level_label"] for b in r.json()["breakdown"]}
        assert "Primary" in labels

    def test_tertiary_present_in_lagos(self, client, facility_set):
        """F3 is tertiary in Lagos."""
        r = client.get(self.url("Lagos"))
        levels = {b["care_level"] for b in r.json()["breakdown"]}
        assert "tertiary" in levels


# ── all LGAs ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFacilityStatsByAllLGAs:
    url = "/api/v1/facilities/stats/by-lga/"

    def test_returns_200(self, client, facility_set):
        assert client.get(self.url).status_code == 200

    def test_correct_lga_count(self, client, facility_set):
        r = client.get(self.url)
        lgas = {row["lga"] for row in r.json()}
        assert lgas == {"Ikeja", "Eti-Osa", "AMAC"}

    def test_each_entry_has_state(self, client, facility_set):
        r = client.get(self.url)
        for row in r.json():
            assert row["state"] != ""

    def test_breakdown_sums_to_total(self, client, facility_set):
        r = client.get(self.url)
        for row in r.json():
            assert sum(b["count"] for b in row["breakdown"]) == row["total"]

    def test_inactive_excluded(self, client, facility_set):
        r = client.get(self.url)
        ikeja = next(row for row in r.json() if row["lga"] == "Ikeja")
        # Ikeja active: F1, F2, F3, F6 = 4
        assert ikeja["total"] == 4


# ── single LGA ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.django_db
class TestFacilityStatsByLGA:
    def url(self, state, lga):
        return f"/api/v1/facilities/stats/by-state/{state}/lgas/{lga}/"

    def test_returns_200_for_known_lga(self, client, facility_set):
        assert client.get(self.url("Lagos", "Ikeja")).status_code == 200

    def test_returns_404_for_unknown_lga(self, client, facility_set):
        assert client.get(self.url("Lagos", "Atlantis")).status_code == 404

    def test_case_insensitive_lookup(self, client, facility_set):
        r = client.get(self.url("Lagos", "ikeja"))
        assert r.status_code == 200
        assert r.json()["lga"] == "Ikeja"

    def test_correct_total(self, client, facility_set):
        r = client.get(self.url("Lagos", "Ikeja"))
        assert r.json()["total"] == 4

    def test_state_populated(self, client, facility_set):
        r = client.get(self.url("Lagos", "Ikeja"))
        assert r.json()["state"] == "Lagos"

    def test_breakdown_sums_to_total(self, client, facility_set):
        r = client.get(self.url("Lagos", "Ikeja"))
        data = r.json()
        assert sum(b["count"] for b in data["breakdown"]) == data["total"]
