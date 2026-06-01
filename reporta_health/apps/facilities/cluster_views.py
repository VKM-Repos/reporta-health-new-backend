"""
Server-side clustering for map display.

GET /api/v1/facilities/clusters/
    ?bbox=min_lng,min_lat,max_lng,max_lat  (required, unless lat/lng provided)
    &zoom=6                                 (required for bbox mode, 1–20)
    &lat=6.52&lng=3.38                      (nearby mode — bypasses zoom logic)
    &radius_km=10                           (optional, default 10, nearby mode only)
    &facility_type=hospital
    &state=Lagos
    &has_sarcs=true
    &has_fistula_programme=true

Nearby mode (lat+lng)     → individual pins ordered by distance
Low zoom   (zoom 1–6)     → one cluster per state
Mid zoom   (zoom 7–11)    → one cluster per LGA
High zoom  (zoom 12+)     → individual facility pins (max 200)
"""
from __future__ import annotations

import logging

from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import Facility
from .serializers import FacilityListSerializer
from .services.spatial import parse_bbox, apply_common_filters
from .services.cache import get_cached, set_cache
from .services.clustering import get_clusters
from .utils.constants import INDIVIDUAL_FACILITY_ZOOM, MAX_INDIVIDUAL_FACILITIES

logger = logging.getLogger(__name__)


class FacilityClusterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes   = [AnonRateThrottle]

    @extend_schema(
        tags=["Map"],
        summary="Facility clusters for map display",
        description=(
            "Nearby mode (lat+lng): returns individual pins ordered by distance. "
            "Browse mode (bbox+zoom): returns state clusters at low zoom, "
            "LGA clusters at mid zoom, individual pins at zoom 12+."
        ),
        parameters=[
            OpenApiParameter("bbox",     OpenApiTypes.STR,   OpenApiParameter.QUERY, description="min_lng,min_lat,max_lng,max_lat"),
            OpenApiParameter("zoom",     OpenApiTypes.INT,   OpenApiParameter.QUERY, description="Map zoom level 1–20"),
            OpenApiParameter("lat",      OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="User latitude (nearby mode)"),
            OpenApiParameter("lng",      OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="User longitude (nearby mode)"),
            OpenApiParameter("radius_km",OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Search radius in km (default 10, nearby mode only)"),
            OpenApiParameter("facility_type",         OpenApiTypes.STR,  OpenApiParameter.QUERY),
            OpenApiParameter("state",                 OpenApiTypes.STR,  OpenApiParameter.QUERY),
            OpenApiParameter("has_sarcs",             OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter("has_fistula_programme", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter("is_verified",           OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        ],
        responses={200: None},
    )
    def get(self, request):
        params = request.query_params

        # ── cache hit ─────────────────────────────────────────────────────────
        cached = get_cached(params)
        if cached:
            logger.info(f"RETURNING CACHED: {cached.get('type')}")
            return Response(cached)

        logger.info(f"CLUSTER REQUEST: {dict(params)}")

        # ── nearby mode ───────────────────────────────────────────────────────
        lat_str = params.get("lat")
        lng_str = params.get("lng")
        if lat_str and lng_str:
            return self._handle_nearby(request, params, lat_str, lng_str)

        # ── browse mode ───────────────────────────────────────────────────────
        return self._handle_browse(request, params)

    # -------------------------------------------------------------------------
    # Nearby mode
    # -------------------------------------------------------------------------

    def _handle_nearby(self, request, params, lat_str, lng_str):
        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except ValueError:
            return Response({"error": "Invalid lat/lng"}, status=400)

        if not (-90 <= lat <= 90):
            return Response({"error": "lat must be between -90 and 90"}, status=400)
        if not (-180 <= lng <= 180):
            return Response({"error": "lng must be between -180 and 180"}, status=400)

        try:
            zoom = int(params.get("zoom", 6))
        except (ValueError, TypeError):
            zoom = 6

        try:
            radius_km = float(params.get("radius_km", 10))
            if radius_km <= 0 or radius_km > 500:
                return Response({"error": "radius_km must be between 0 and 500"}, status=400)
        except (ValueError, TypeError):
            return Response({"error": "Invalid radius_km"}, status=status.HTTP_400_BAD_REQUEST)

        user_point = Point(lng, lat, srid=4326)
        qs = (
            Facility.objects
            .filter(is_active=True, location__distance_lte=(user_point, D(km=radius_km)))
            .annotate(distance=Distance("location", user_point))
            .order_by("distance")
        )
        qs = apply_common_filters(qs, params)
        count = len(qs.only("id")[:31])

        if zoom >= INDIVIDUAL_FACILITY_ZOOM or count <= 30:
            logger.info(f"NEARBY DECISION: individual — zoom {zoom}, count {count}")
            response_data = self._individual_response(qs, request).data
        else:
            logger.info(f"NEARBY DECISION: clusters — zoom {zoom}, count {count}")
            response_data = get_clusters(qs, zoom)

        set_cache(params, response_data, nearby=True)
        return Response(response_data)

    # -------------------------------------------------------------------------
    # Browse mode
    # -------------------------------------------------------------------------

    def _handle_browse(self, request, params):
        bbox_str = params.get("bbox", "").strip()
        if not bbox_str:
            return Response(
                {"error": "Provide either lat+lng (nearby) or bbox+zoom (browse)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bounding_box = parse_bbox(bbox_str)
        if bounding_box is None:
            return Response(
                {"error": "Invalid bbox. Format: min_lng,min_lat,max_lng,max_lat"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            zoom = int(params.get("zoom", 0))
            if not (1 <= zoom <= 20):
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "zoom must be an integer between 1 and 20"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Facility.objects.filter(is_active=True, location__within=bounding_box)
        qs = apply_common_filters(qs, params)
        count = len(qs.only("id")[:31])

        if zoom >= INDIVIDUAL_FACILITY_ZOOM or count <= 30:
            logger.info(f"BROWSE DECISION: individual — zoom {zoom}, count {count}")
            response_data = self._individual_response(qs, request).data
        else:
            logger.info(f"BROWSE DECISION: clusters — zoom {zoom}, count {count}")
            response_data = get_clusters(qs, zoom)

        set_cache(params, response_data)
        return Response(response_data)

    # -------------------------------------------------------------------------
    # Individual pins
    # -------------------------------------------------------------------------

    def _individual_response(self, qs, request):
        qs = qs.select_related("sarc_profile").prefetch_related("images")
        if not qs.ordered:
            qs = qs.order_by("id")
        qs = qs[:MAX_INDIVIDUAL_FACILITIES]
        serializer = FacilityListSerializer(qs, many=True, context={"request": request})
        return Response({
            "type":    "facilities",
            "count":   len(serializer.data),
            "results": serializer.data,
        })