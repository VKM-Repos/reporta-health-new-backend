"""
Views for GBV app.
"""
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db.models import Q
from django.contrib.postgres.indexes import GistIndex
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.facilities.models import Facility
from .models import GBVService
from .serializers import GBVServiceSerializer

DEFAULT_RADIUS_KM = 50
MAX_RADIUS_KM     = 200
MAX_NEARBY_RESULTS = 100
CACHE_TIMEOUT      = 60 * 5  # 5 minutes


def _validate_lat_lng(lat_str, lng_str):
    """Validate and parse lat/lng strings. Returns (lat, lng) or raises ValueError."""
    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except (TypeError, ValueError):
        raise ValueError("lat and lng are required")

    if not (-90 <= lat <= 90):
        raise ValueError("lat must be between -90 and 90")
    if not (-180 <= lng <= 180):
        raise ValueError("lng must be between -180 and 180")

    return lat, lng


def _validate_radius(radius_str):
    """Validate radius_km. Returns float or raises ValueError."""
    try:
        radius_km = float(radius_str or DEFAULT_RADIUS_KM)
        if radius_km <= 0 or radius_km > MAX_RADIUS_KM:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError(f"radius_km must be between 0 and {MAX_RADIUS_KM}")
    return radius_km


# ---------------------------------------------------------------------------
# GBV Services list
# ---------------------------------------------------------------------------

class GBVServiceListView(generics.ListAPIView):
    """
    GET /api/v1/gbv/services/
    List all GBV services with optional filtering.
    """
    serializer_class   = GBVServiceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = StandardPagination

    def get_queryset(self):
        qs    = GBVService.objects.filter(is_active=True)
        state = self.request.query_params.get('state')
        lga   = self.request.query_params.get('lga')
        org   = self.request.query_params.get('organisation_type')

        if state:
            qs = qs.filter(state__iexact=state)
        if lga:
            qs = qs.filter(lga__iexact=lga)
        if org:
            qs = qs.filter(organisation_type=org)

        return qs


# ---------------------------------------------------------------------------
# GBV Services nearby
# ---------------------------------------------------------------------------

class GBVServiceNearbyView(APIView):
    """
    GET /api/v1/gbv/services/nearby/?lat=&lng=&radius_km=
    GBV services ordered by distance from user.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["GBV"],
        summary="Nearby GBV services",
        parameters=[
            OpenApiParameter("lat",       OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("lng",       OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("radius_km", OpenApiTypes.FLOAT, OpenApiParameter.QUERY),
            OpenApiParameter("state",     OpenApiTypes.STR,   OpenApiParameter.QUERY),
        ],
        responses={200: GBVServiceSerializer(many=True)},
    )
    def get(self, request):
        try:
            lat, lng  = _validate_lat_lng(
                request.query_params.get('lat'),
                request.query_params.get('lng'),
            )
            radius_km = _validate_radius(request.query_params.get('radius_km'))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user_point = Point(lng, lat, srid=4326)

        qs = (
            GBVService.objects
            .only(
                "id", "name", "state", "lga", "organisation_type",
                "services", "target_group", "address", "phone_number",
                "contact_person", "accessibility_info", "operating_hours",
                "location", "is_active",
            )
            .filter(
                is_active=True,
                location__isnull=False,
                location__distance_lte=(user_point, D(km=radius_km)),
            )
            .annotate(distance=Distance('location', user_point))
            .order_by('distance')
        )

        state = request.query_params.get('state')
        if state:
            qs = qs.filter(state__iexact=state)

        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = GBVServiceSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


# ---------------------------------------------------------------------------
# Combined nearby — SARCs + GBV services (for Report Now button)
# ---------------------------------------------------------------------------

class GBVNearbyView(APIView):
    """
    GET /api/v1/gbv/nearby/?lat=&lng=&radius_km=
    Returns both SARC facilities and GBV services ordered by distance.
    This is the endpoint for the Report Now button.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["GBV"],
        summary="Nearby GBV help — combined SARCs and services",
        parameters=[
            OpenApiParameter("lat",       OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("lng",       OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("radius_km", OpenApiTypes.FLOAT, OpenApiParameter.QUERY),
        ],
        responses={200: None},
    )
    def get(self, request):
        try:
            lat, lng  = _validate_lat_lng(
                request.query_params.get('lat'),
                request.query_params.get('lng'),
            )
            radius_km = _validate_radius(request.query_params.get('radius_km'))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # check cache first
        cache_key = f"gbv_nearby:{round(lat, 3)}:{round(lng, 3)}:{radius_km}"
        cached    = cache.get(cache_key)
        if cached:
            return Response(cached)

        user_point      = Point(lng, lat, srid=4326)
        distance_filter = D(km=radius_km)

        # --- GBV services ---
        gbv_qs = (
            GBVService.objects
            .only(
                "id", "name", "state", "lga", "address", "phone_number",
                "services", "location", "organisation_type", "target_group",
                "operating_hours", "accessibility_info", "contact_person",
            )
            .filter(
                is_active=True,
                location__isnull=False,
                location__distance_lte=(user_point, distance_filter),
            )
            .annotate(distance=Distance('location', user_point))
            .order_by('distance')[:MAX_NEARBY_RESULTS]
        )

        # --- SARC facilities ---
        sarc_qs = (
            Facility.objects
            .only(
                "id", "name", "state", "lga", "address", "phone_number",
                "facility_type", "has_sarcs", "location",
            )
            .filter(
                is_active=True,
                location__isnull=False,
                location__distance_lte=(user_point, distance_filter),
            )
            .filter(Q(facility_type='sarcs') | Q(has_sarcs=True))
            .annotate(distance=Distance('location', user_point))
            .select_related('sarc_profile')
            .order_by('distance')[:MAX_NEARBY_RESULTS]
        )

        # --- combine and sort by distance ---
        results = []

        for s in gbv_qs:
            results.append({
                "kind":         "gbv_service",
                "id":           s.id,
                "name":         s.name,
                "state":        s.state,
                "lga":          s.lga,
                "address":      s.address,
                "phone_number": s.phone_number,
                "services":     s.services,
                "distance_m":   round(s.distance.m, 1),
                "location": {
                    "latitude":  s.location.y,
                    "longitude": s.location.x,
                },
                "extra": {
                    "organisation_type":  s.organisation_type,
                    "target_group":       s.target_group,
                    "operating_hours":    s.operating_hours,
                    "accessibility_info": s.accessibility_info,
                    "contact_person":     s.contact_person,
                },
            })

        for f in sarc_qs:
            profile = getattr(f, 'sarc_profile', None)
            results.append({
                "kind":         "sarc",
                "id":           f.id,
                "name":         f.name,
                "state":        f.state,
                "lga":          f.lga,
                "address":      f.address,
                "phone_number": f.phone_number,
                "services":     profile.additional_info if profile else "",
                "distance_m":   round(f.distance.m, 1),
                "location": {
                    "latitude":  f.location.y,
                    "longitude": f.location.x,
                },
                "extra": {
                    "unit_name":      profile.unit_name if profile else "",
                    "hotline_number": profile.hotline_number if profile else "",
                    "has_legal_aid":  profile.has_legal_aid if profile else False,
                    "has_counseling": profile.has_counseling if profile else False,
                    "has_hiv_pep":    profile.has_hiv_pep if profile else False,
                },
            })

        results.sort(key=lambda x: x['distance_m'])

        response_data = {
            "count":   len(results),
            "results": results,
        }

        cache.set(cache_key, response_data, CACHE_TIMEOUT)
        return Response(response_data)