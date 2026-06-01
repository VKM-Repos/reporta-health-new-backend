"""
Tests for the facility clustering endpoint.

GET /api/v1/facilities/clusters/?bbox=&zoom=   (browse mode)
GET /api/v1/facilities/clusters/?lat=&lng=     (nearby mode)
"""
import pytest
from django.contrib.gis.geos import Point
from django.core.cache import cache

from apps.facilities.models import Facility

CLUSTER_URL = "/api/v1/facilities/clusters/"

# Bounding boxes
NIGERIA_BBOX = "2.5,4.0,15.0,14.0"
LAGOS_BBOX   = "3.0,6.3,3.8,6.7"
EMPTY_BBOX   = "-30.0,0.0,-10.0,10.0"  # Atlantic Ocean — no facilities


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_facility(state, lat, lng, **kwargs):
    """Directly create a single Facility. kwargs override any field."""
    return Facility.objects.create(
        name=kwargs.pop("name", f"Facility {state}"),
        facility_type=kwargs.pop("facility_type", "hospital"),
        ownership=kwargs.pop("ownership", "private"),
        care_level=kwargs.pop("care_level", "primary"),
        address=kwargs.pop("address", "1 Test St"),
        lga=kwargs.pop("lga", state),
        state=state,
        location=Point(lng, lat, srid=4326),
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )


def make_facilities_in_state(state, count, base_lat, base_lng, **kwargs):
    """Bulk-create `count` facilities spread across a state."""
    Facility.objects.bulk_create([
        Facility(
            name=f"{state} Facility {i}",
            facility_type="hospital" if i % 2 == 0 else "clinic",
            ownership="private",
            care_level="primary",
            address=f"{i} Test St",
            state=state,
            lga=state,
            location=Point(base_lng + i * 0.001, base_lat + i * 0.001, srid=4326),
            is_active=True,
            **kwargs,
        )
        for i in range(count)
    ])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def three_state_dataset(db):
    """
    120 active facilities spread across Lagos, FCT, and Kano (40 each).
    Plus one inactive Lagos facility to test exclusion.
    """
    make_facilities_in_state("Lagos", 40, base_lat=6.52, base_lng=3.37)
    make_facilities_in_state("FCT",   40, base_lat=9.05, base_lng=7.49)
    make_facilities_in_state("Kano",  40, base_lat=12.0, base_lng=8.52)
    make_facility("Lagos", lat=6.52, lng=3.37, name="Inactive", is_active=False)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestValidation:

    def test_missing_bbox_and_latlng_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"zoom": 6})
        assert r.status_code == 400

    def test_missing_zoom_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX})
        assert r.status_code == 400
        assert "zoom" in r.data["error"]

    def test_invalid_bbox_string_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": "not,a,valid,bbox", "zoom": 6})
        assert r.status_code == 400

    def test_bbox_wrong_part_count_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": "3.0,6.3,3.8", "zoom": 6})
        assert r.status_code == 400

    def test_zoom_out_of_range_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 99})
        assert r.status_code == 400

    def test_zoom_zero_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 0})
        assert r.status_code == 400

    def test_non_integer_zoom_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": "fast"})
        assert r.status_code == 400

    def test_invalid_lat_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"lat": "bad", "lng": "3.38"})
        assert r.status_code == 400

    def test_invalid_radius_km_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"lat": "6.52", "lng": "3.38", "radius_km": "-5"})
        assert r.status_code == 400

    def test_radius_km_too_large_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"lat": "6.52", "lng": "3.38", "radius_km": "9999"})
        assert r.status_code == 400

    def test_anonymous_user_can_access(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Browse mode — low zoom → clusters
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBrowseModeClusters:

    def test_returns_clusters_type(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert r.status_code == 200
        assert r.data["type"] == "clusters"

    def test_results_is_list(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert isinstance(r.data["results"], list)

    def test_count_key_present(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert "count" in r.data

    def test_zoom_returned_in_response(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 7})
        assert r.data["zoom"] == 7

    def test_cluster_items_have_required_fields(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert len(r.data["results"]) > 0
        for item in r.data["results"]:
            for field in ("type", "lat", "lng", "count", "density_level"):
                assert field in item, f"Missing field: {field}"

    def test_cluster_items_type_field_is_cluster(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        for item in r.data["results"]:
            assert item["type"] == "cluster"

    def test_density_level_valid_values(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        for item in r.data["results"]:
            assert item["density_level"] in ("low", "medium", "high")

    def test_state_clusters_have_label(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        for item in r.data["results"]:
            assert item["label"] is not None
            assert len(item["label"]) > 0

    def test_three_states_in_response(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        assert r.data["count"] == 3

    def test_inactive_facilities_excluded(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        total = sum(item["count"] for item in r.data["results"])
        assert total == 120  # 40 × 3 states, inactive excluded

    def test_bbox_restricts_to_lagos_only(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": LAGOS_BBOX, "zoom": 6})
        total = sum(item["count"] for item in r.data["results"])
        assert total == 40

    def test_empty_bbox_returns_empty(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": EMPTY_BBOX, "zoom": 6})
        assert r.status_code == 200
        assert r.data["count"] == 0
        assert r.data["results"] == []


# ---------------------------------------------------------------------------
# Browse mode — high zoom → individual facilities
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBrowseModeIndividual:

    def test_zoom_12_returns_facilities_type(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        assert r.status_code == 200
        assert r.data["type"] == "facilities"

    def test_zoom_14_returns_facilities_type(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 14})
        assert r.data["type"] == "facilities"

    def test_zoom_11_returns_clusters(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 11})
        assert r.data["type"] == "clusters"

    def test_results_is_list(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        assert isinstance(r.data["results"], list)

    def test_facility_objects_have_required_fields(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        assert len(r.data["results"]) > 0
        for field in ("id", "name", "facility_type", "state"):
            assert field in r.data["results"][0], f"Missing field: {field}"

    def test_inactive_excluded(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        names = [f["name"] for f in r.data["results"]]
        assert "Inactive" not in names

    def test_bbox_restricts_results(self, api_client, three_state_dataset):
        r_lagos = api_client.get(CLUSTER_URL, {"bbox": LAGOS_BBOX, "zoom": 12})
        r_all   = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        assert r_lagos.data["count"] < r_all.data["count"]


# ---------------------------------------------------------------------------
# Nearby mode
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNearbyMode:

    def test_returns_200(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"lat": "6.52", "lng": "3.38"})
        assert r.status_code == 200

    def test_high_zoom_returns_facilities(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {"lat": "6.52", "lng": "3.38", "zoom": "13"})
        assert r.data["type"] == "facilities"

    def test_low_zoom_large_radius_returns_clusters(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {
            "lat": "9.0", "lng": "8.0", "zoom": "5", "radius_km": "500"
            # "lat": "9.0", "lng": "8.0", "zoom": "6", "radius_km": "1000"
        })
        assert r.data["type"] == "clusters"

    def test_small_radius_restricts_to_nearby_state(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {
            "lat": "6.52", "lng": "3.38", "zoom": "13", "radius_km": "10"
        })
        assert r.data["type"] == "facilities"
        states = {f["state"] for f in r.data["results"]}
        assert states == {"Lagos"}

    def test_inactive_excluded(self, api_client, three_state_dataset):
        r = api_client.get(CLUSTER_URL, {
            "lat": "6.52", "lng": "3.38", "zoom": "13", "radius_km": "100"
        })
        names = [f["name"] for f in r.data["results"]]
        assert "Inactive" not in names

    def test_invalid_lat_returns_400(self, api_client):
        r = api_client.get(CLUSTER_URL, {"lat": "abc", "lng": "3.38"})
        assert r.status_code == 400

    def test_latlng_takes_priority_over_bbox(self, api_client, three_state_dataset):
        """When both lat/lng and bbox are supplied, nearby mode wins."""
        r = api_client.get(CLUSTER_URL, {
            "lat": "6.52", "lng": "3.38",
            "bbox": NIGERIA_BBOX, "zoom": "13",
        })
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFilters:

    def test_filter_by_facility_type_in_cluster_mode(self, api_client, db):
        """Use enough facilities to trigger cluster mode."""
        for i in range(35):
            make_facility("Lagos", lat=6.52 + i * 0.001, lng=3.37 + i * 0.001,
                        facility_type="hospital")
        for i in range(35):
            make_facility("Lagos", lat=6.52 + i * 0.001, lng=3.47 + i * 0.001,
                        facility_type="clinic")
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 6, "facility_type": "hospital"
        })
        assert r.status_code == 200
        total = sum(item["count"] for item in r.data["results"])
        assert total == 35

    def test_filter_by_facility_type_in_individual_mode(self, api_client, db):
        make_facility("Lagos", lat=6.52, lng=3.37, facility_type="hospital")
        make_facility("Lagos", lat=6.53, lng=3.38, facility_type="clinic")
        make_facility("FCT",   lat=9.05, lng=7.49, facility_type="hospital")
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "facility_type": "hospital"
        })
        assert r.data["count"] == 2

    def test_filter_by_state(self, api_client, db):
        make_facility("Lagos", lat=6.52, lng=3.37)
        make_facility("FCT",   lat=9.05, lng=7.49)
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "state": "Lagos"
        })
        assert r.data["count"] == 1
        assert r.data["results"][0]["state"] == "Lagos"

    def test_filter_by_state_case_insensitive(self, api_client, db):
        make_facility("Lagos", lat=6.52, lng=3.37)
        make_facility("FCT",   lat=9.05, lng=7.49)
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "state": "lagos"
        })
        assert r.data["count"] == 1

    def test_filter_has_sarcs(self, api_client, db):
        f1 = make_facility("Lagos", lat=6.52, lng=3.37, has_sarcs=True)
        make_facility("Lagos", lat=6.53, lng=3.38, has_sarcs=False)
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "has_sarcs": "true"
        })
        assert r.data["count"] == 1
        assert r.data["results"][0]["id"] == f1.pk

    def test_filter_has_fistula_programme(self, api_client, db):
        f1 = make_facility("FCT", lat=9.05, lng=7.49, has_fistula_programme=True)
        make_facility("FCT", lat=9.06, lng=7.50, has_fistula_programme=False)
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "has_fistula_programme": "true"
        })
        assert r.data["count"] == 1
        assert r.data["results"][0]["id"] == f1.pk

    def test_filter_is_verified(self, api_client, db):
        f1 = make_facility("Lagos", lat=6.52, lng=3.37, is_verified=True)
        make_facility("Lagos", lat=6.53, lng=3.38, is_verified=False)
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12, "is_verified": "true"
        })
        assert r.data["count"] == 1
        assert r.data["results"][0]["id"] == f1.pk

    def test_combined_filters(self, api_client, db):
        f1 = make_facility("Lagos", lat=6.52, lng=3.37,
                           has_sarcs=True, facility_type="hospital")
        make_facility("Lagos", lat=6.53, lng=3.38,
                      facility_type="clinic")
        make_facility("FCT", lat=9.05, lng=7.49,
                      has_sarcs=True, facility_type="hospital")
        r = api_client.get(CLUSTER_URL, {
            "bbox": NIGERIA_BBOX, "zoom": 12,
            "has_sarcs": "true", "state": "Lagos",
        })
        assert r.data["count"] == 1
        assert r.data["results"][0]["id"] == f1.pk


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCache:

    def test_same_request_returns_same_data(self, api_client, three_state_dataset):
        params = {"bbox": NIGERIA_BBOX, "zoom": 12}
        r1 = api_client.get(CLUSTER_URL, params)
        r2 = api_client.get(CLUSTER_URL, params)
        assert r1.status_code == 200
        assert r1.data == r2.data

    def test_different_zoom_returns_different_type(self, api_client, three_state_dataset):
        r_clusters    = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 6})
        r_individuals = api_client.get(CLUSTER_URL, {"bbox": NIGERIA_BBOX, "zoom": 12})
        assert r_clusters.data["type"] != r_individuals.data["type"]