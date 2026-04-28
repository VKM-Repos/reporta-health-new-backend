"""
SARC (Sexual Assault Referral Centre) views
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.core.pagination import StandardPagination
from .models import Facility
from .sarc_serializers import SARCFacilitySerializer

MAX_RADIUS = 50_000  # 50km cap

VALID_SERVICES = {
    'legal_aid': 'sarc_profile__has_legal_aid',
    'counseling': 'sarc_profile__has_counseling',
    'hiv_pep': 'sarc_profile__has_hiv_pep',
    'police_support': 'sarc_profile__has_police_presence',
    'emergency_contraception': 'sarc_profile__has_emergency_contraception',
    'shelter_referral': 'sarc_profile__has_shelter_referral',
    'forensic': 'sarc_profile__has_forensic',
    'sti_testing': 'sarc_profile__has_sti_testing',
    'court_support': 'sarc_profile__has_court_support',
}


def _sarc_queryset():
    """Base queryset for SARC facilities — standalone or hospital with SARC unit."""
    return (
        Facility.objects.filter(is_active=True)
        .filter(Q(facility_type='sarcs') | Q(has_sarcs=True))
        .select_related('sarc_profile')
        .prefetch_related('images')
    )


class SARCListView(APIView):
    """
    GET /api/facilities/sarcs/
    List all SARC facilities — standalone centres and hospitals with SARC units.
    Supports optional nearby search via lat/lng/radius.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["SARC"],
        summary="List all SARC facilities",
        description=(
            "Returns standalone Sexual Assault Referral Centres and hospitals "
            "that have a SARC unit. Optionally filter by proximity."
        ),
        parameters=[
            OpenApiParameter("lat", OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY,
                             description="Latitude for nearby search"),
            OpenApiParameter("lng", OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY,
                             description="Longitude for nearby search"),
            OpenApiParameter("radius", OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description=f"Search radius in metres (default 10000, max {MAX_RADIUS})"),
            OpenApiParameter("state", OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description="Filter by state name"),
            OpenApiParameter("service", OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description=f"Filter by service. Valid values: {', '.join(VALID_SERVICES)}"),
        ],
        responses={200: SARCFacilitySerializer(many=True)},
    )
    def get(self, request):
        qs = _sarc_queryset()

        # State filter
        state = request.query_params.get('state')
        if state:
            qs = qs.filter(state__iexact=state)

        # Service filter — return 400 for unknown service
        service = request.query_params.get('service')
        if service:
            if service not in VALID_SERVICES:
                return Response(
                    {
                        'error': f"Invalid service '{service}'.",
                        'valid_services': list(VALID_SERVICES.keys()),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(**{VALID_SERVICES[service]: True})

        # Nearby search
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                radius = min(
                    int(request.query_params.get('radius', 10000)),
                    MAX_RADIUS  # cap radius
                )
                user_location = Point(lng, lat, srid=4326)
                qs = qs.filter(
                    location__distance_lte=(user_location, D(m=radius))
                ).annotate(
                    distance=Distance('location', user_location)
                ).order_by('distance')
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid lat/lng coordinates.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            qs = qs.order_by('state', 'name')

        # Pagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = SARCFacilitySerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class SARCDetailView(APIView):
    """
    GET /api/facilities/sarcs/<int:pk>/
    Get full SARC facility detail including profile.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["SARC"],
        summary="Get SARC facility detail",
        responses={200: SARCFacilitySerializer},
    )
    def get(self, request, pk):
        try:
            facility = _sarc_queryset().get(pk=pk)
        except Facility.DoesNotExist:
            return Response(
                {'detail': 'SARC facility not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = SARCFacilitySerializer(facility, context={'request': request})
        return Response(serializer.data)