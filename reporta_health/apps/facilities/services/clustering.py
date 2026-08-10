"""
Clustering strategies for facility map display.
Handles state, LGA, grid, and fallback clustering.
"""
import logging

from django.db.models import Avg, Count
from django.db.utils import DatabaseError

from apps.facilities.utils.constants import MAX_CLUSTERS, STATE_CENTROIDS, MIN_CLUSTER_SIZE
from apps.facilities.services.spatial import ST_Y, ST_X, density_level

logger = logging.getLogger(__name__)


def get_clusters(qs, zoom) -> dict:
    """Entry point — returns a full cluster response dict."""
    try:
        clusters = _group_by_field(qs)
    except DatabaseError as e:
        logger.exception(f"State clustering failed, falling back: {e}")
        clusters = _fallback_clusters(qs)

    return {
        "type":    "clusters",
        "zoom":    zoom,
        "count":   len(clusters),
        "results": clusters,
    }

def _group_by_field(qs) -> list:
    """
    Group by state using average lat/lng as bubble centre.
    Falls back to STATE_CENTROIDS when avg coords are null.
    """
    field = "state"
    rows = (
        qs.filter(**{f"{field}__isnull": False})
        .exclude(**{field: ""})
        .values(field)
        .annotate(
            count=Count("id"),
            avg_rating=Avg("average_rating"),
            lat=Avg(ST_Y("location")),
            lng=Avg(ST_X("location")),
        )
        .order_by("-count")[:MAX_CLUSTERS]
    )

    results = []
    for row in rows:
        lat = row["lat"]
        lng = row["lng"]

        if (lat is None or lng is None) and field == "state":
            centroid = STATE_CENTROIDS.get(row[field])
            if centroid is None:
                continue
            lat, lng = centroid

        if lat is None or lng is None:
            continue

        results.append({
            "type":          "cluster",
            "label":         row[field],
            "lat":           round(float(lat), 4),
            "lng":           round(float(lng), 4),
            "count":         row["count"],
            "avg_rating":    round(float(row["avg_rating"]), 2) if row["avg_rating"] is not None else None,
            "bounds":        None,
            "density_level": density_level(row["count"]),
        })
    return results


def _fallback_clusters(qs) -> list:
    """Emergency fallback — groups by state using hardcoded centroids."""
    rows = (
        qs.exclude(state__isnull=True)
        .exclude(state="")
        .values("state")
        .annotate(count=Count("id"), avg_rating=Avg("average_rating"))
        .order_by("-count")[:MAX_CLUSTERS]
    )

    results = []
    for row in rows:
        centroid = STATE_CENTROIDS.get(row["state"])
        if centroid is None:
            continue
        results.append({
            "type":          "cluster",
            "label":         row["state"],
            "lat":           centroid[0],
            "lng":           centroid[1],
            "count":         row["count"],
            "avg_rating":    round(float(row["avg_rating"]), 2) if row["avg_rating"] is not None else None,
            "bounds":        None,
            "density_level": density_level(row["count"]),
        })
    return results