"""
SARC (Sexual Assault Referral Centre) views
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Prefetch
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Facility, SARCProfile
from .sarc_serializers import SARCFacilitySerializer


def _sarc_queryset():
    """Base queryset for SARC facilities — standalone or hospital with SARC unit."""
    return (
        Facility.objects.filter(
            is_active=True
        ).filter(
            Q(facility_type='sarcs') | Q(has_sarcs=True)
        ).select_related('sarc_profile')
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
                           description="Search radius in metres (default 10000)"),
            OpenApiParameter("state", OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                           description="Filter by state name"),
            OpenApiParameter("service", OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                           description="Filter by service: legal_aid, counseling, hiv_pep, police_support etc."),
        ],
        responses={200: SARCFacilitySerializer(many=True)},
    )
    def get(self, request):
        qs = _sarc_queryset()

        # State filter
        state = request.query_params.get('state')
        if state:
            qs = qs.filter(state__iexact=state)

        # Service filter
        service = request.query_params.get('service')
        service_field_map = {
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
        if service and service in service_field_map:
            qs = qs.filter(**{service_field_map[service]: True})

        # Nearby search
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                radius = int(request.query_params.get('radius', 10000))
                user_location = Point(lng, lat, srid=4326)
                qs = qs.filter(
                    location__distance_lte=(user_location, D(m=radius))
                ).annotate(
                    distance=Distance('location', user_location)
                ).order_by('distance')
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid lat/lng coordinates'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            qs = qs.order_by('state', 'name')

        serializer = SARCFacilitySerializer(qs, many=True, context={'request': request})
        return Response({
            'count': qs.count(),
            'results': serializer.data
        })


class SARCDetailView(APIView):
    """
    GET /api/facilities/sarcs/<id>/
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