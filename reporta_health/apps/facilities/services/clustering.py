"""
Clustering strategies for facility map display.
Handles state, LGA, grid, and fallback clustering.
"""
import logging

from django.db import connection
from django.db.models import Avg, Count
from django.db.utils import DatabaseError

from apps.facilities.utils.constants import MAX_CLUSTERS, STATE_CENTROIDS, ZOOM_GRID
from apps.facilities.services.spatial import ST_Y, ST_X, density_level

logger = logging.getLogger(__name__)


def get_clusters(qs, zoom) -> dict:
    """Entry point — returns a full cluster response dict."""
    grid_size = ZOOM_GRID.get(zoom, ZOOM_GRID[1])

    try:
        clusters = _postgis_clusters(qs, grid_size)
    except DatabaseError as e:
        logger.exception(f"PostGIS clustering failed, falling back: {e}")
        clusters = _fallback_clusters(qs)

    return {
        "type":    "clusters",
        "zoom":    zoom,
        "count":   len(clusters),
        "results": clusters,
    }


def _postgis_clusters(qs, grid_size: float) -> list:
    if grid_size >= 1.0:
        return _group_by_field(qs, "state")

    if grid_size >= 0.1:
        clusters = _group_by_field(qs, "lga")
        return clusters or _group_by_field(qs, "state")

    return _snap_to_grid(qs, grid_size)


def _group_by_field(qs, field: str) -> list:
    """
    Group by state or LGA using average lat/lng as bubble centre.
    Falls back to STATE_CENTROIDS only for state when avg coords are null.
    """
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


def _snap_to_grid(qs, grid_size: float) -> list:
    """Fine-grained geometric clustering via ST_SnapToGrid (zoom 10-11)."""
    subquery, sub_params = qs.values("id").query.sql_with_params()

    sql = f"""
        SELECT
            ST_Y(ST_Centroid(ST_Collect(location::geometry))) AS cluster_lat,
            ST_X(ST_Centroid(ST_Collect(location::geometry))) AS cluster_lng,
            COUNT(*)                                           AS point_count,
            AVG(average_rating)                               AS avg_rating,
            ST_XMin(ST_Extent(location::geometry))            AS cell_min_lng,
            ST_YMin(ST_Extent(location::geometry))            AS cell_min_lat,
            ST_XMax(ST_Extent(location::geometry))            AS cell_max_lng,
            ST_YMax(ST_Extent(location::geometry))            AS cell_max_lat
        FROM facilities_facility
        WHERE id IN ({subquery})
            AND location IS NOT NULL
        GROUP BY ST_SnapToGrid(location::geometry, %s)
        ORDER BY point_count DESC
        LIMIT %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, list(sub_params) + [grid_size, MAX_CLUSTERS])
        rows = cursor.fetchall()

    return [
        {
            "type":          "cluster",
            "label":         None,
            "lat":           float(row[0]),
            "lng":           float(row[1]),
            "count":         row[2],
            "avg_rating":    round(float(row[3]), 2) if row[3] is not None else None,
            "density_level": density_level(row[2]),
            "bounds": {
                "min_lng": float(row[4]),
                "min_lat": float(row[5]),
                "max_lng": float(row[6]),
                "max_lat": float(row[7]),
            } if row[4] is not None else None,
        }
        for row in rows
    ]


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