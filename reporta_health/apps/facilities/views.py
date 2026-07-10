"""
Views for Facility endpoints with geospatial queries
"""

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django_filters.rest_framework import DjangoFilterBackend
from .models import Facility, FacilityImage, FacilityViewHistory, FacilityBookmark
from .serializers import (
    FacilityListSerializer,
    FacilityDetailSerializer,
    FacilityCreateSerializer,
    FacilityImageSerializer,
    FacilityViewHistorySerializer,
    FacilityBookmarkSerializer,
)
from .filters import FacilityFilter
from .services.spatial import apply_common_filters
from django.db.models import Prefetch
from apps.reviews.models import Review
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter,inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework import serializers as drf_serializers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Prefetch

class FacilityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'  
    max_page_size = 100                 

class FacilityListView(generics.ListAPIView):
    """
    List all facilities with filtering and search
    GET /api/facilities/
    
    Query parameters:
    - facility_type: Filter by type (hospital, clinic, etc.)
    - search: Search by name
    - ordering: Order by field (e.g., -average_rating, name)
    - is_verified: Filter by verified status
    """
    queryset = Facility.objects.filter(is_active=True).prefetch_related(
    Prefetch('images', queryset=FacilityImage.objects.filter(is_primary=True))
)
    serializer_class = FacilityListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FacilityFilter
    search_fields = ['name', 'description', 'services', 'address']
    ordering_fields = ['name', 'average_rating', 'created_at', 'total_reviews']
    ordering = ['-average_rating']
    pagination_class = FacilityPagination  


@extend_schema(
    parameters=[
        OpenApiParameter("lat", OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY, required=True, description="Latitude"),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY, required=True, description="Longitude"),
        OpenApiParameter("radius", OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Search radius in meters"),
        OpenApiParameter("limit", OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Max results"),
    ],
    responses={200: FacilityListSerializer(many=True)},
    description="Get facilities near a specific location"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def nearby_facilities(request):
    """
    Get facilities near a specific location
    GET /api/facilities/nearby/
    
    Required query parameters:
    - lat: Latitude
    - lng: Longitude
    - radius: Search radius in meters (optional, default 5000)
    
    Optional:
    - facility_type: Filter by type
    - limit: Max results (default 20)
    """
    # Get coordinates from query params
    try:
        latitude = float(request.query_params.get('lat'))
        longitude = float(request.query_params.get('lng'))
    except (TypeError, ValueError):
        return Response(
            {'error': 'Invalid latitude or longitude'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get search radius (default 10km, matches cluster view)
    try:
        radius_km = float(request.query_params.get('radius_km', 10))
    except ValueError:
        radius_km = 10
    
    # Create user location point
    user_location = Point(longitude, latitude, srid=4326)
    
    # Query facilities within radius
    queryset = Facility.objects.filter(
        is_active=True,
        location__distance_lte=(user_location, D(km=radius_km))
    ).annotate(
        distance=Distance('location', user_location)
    ).select_related().prefetch_related('images').order_by('distance')
    
    # Apply all common filters (facility_type, state, has_gbv_services, has_sarcs, has_fistula_programme)
    queryset = apply_common_filters(queryset, request.query_params)
    
    # Apply limit
    try:
        limit = int(request.query_params.get('limit', 20))
        # limit = int(limit_param) if limit_param else 20
    except (ValueError, TypeError):
        limit = 20
    # limit = int(request.query_params.get('limit', 20))
    queryset = queryset[:limit]
    
    # Serialize and return
    serializer = FacilityListSerializer(
        queryset,
        many=True,
        context={'request': request}
    )
    
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    })


class FacilityDetailView(generics.RetrieveAPIView):
    """
    Get facility details
    GET /api/facilities/:id/
    """
    queryset = Facility.objects.filter(is_active=True).prefetch_related('images', Prefetch('reviews', queryset=Review.objects.only('id', 'rating')))
    serializer_class = FacilityDetailSerializer
    permission_classes = [permissions.AllowAny]


class FacilityCreateView(generics.CreateAPIView):
    """
    Create a new facility (admin only)
    POST /api/facilities/
    """
    queryset = Facility.objects.all()
    serializer_class = FacilityCreateSerializer
    permission_classes = [permissions.IsAdminUser]


class FacilityUpdateView(generics.UpdateAPIView):
    """
    Update facility (admin only)
    PUT/PATCH /api/facilities/:id/
    """
    queryset = Facility.objects.all()
    serializer_class = FacilityCreateSerializer
    permission_classes = [permissions.IsAdminUser]

@extend_schema(responses={204: None})
class FacilityDeleteView(generics.DestroyAPIView):
    """
    Delete facility (admin only)
    DELETE /api/facilities/:id/
    """
    queryset = Facility.objects.all()
    permission_classes = [permissions.IsAdminUser]


class FacilityImageUploadView(generics.CreateAPIView):
    """
    Upload image for a facility
    POST /api/facilities/:facility_id/images/
    """
    serializer_class = FacilityImageSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        facility_id = self.kwargs.get('facility_id')
        facility = get_object_or_404(Facility, id=facility_id)
        serializer.save(facility=facility)
        serializer.save(facility_id=facility_id)


@extend_schema(
    tags=["Facilities"],
    summary="List all facility type choices",
    responses={200: inline_serializer(
        name='FacilityType',
        fields={
            'value': drf_serializers.CharField(),
            'label': drf_serializers.CharField(),
        }
    )}
)
class FacilityTypesView(APIView):
    """
    List all facility type choices
    GET /api/facilities/types/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = [
            {'value': value, 'label': label}
            for value, label in Facility.FACILITY_TYPES
        ]
        return Response(data)

@extend_schema(
    tags=["Facilities"],
    summary="List all states with active facilities",
    responses={200: inline_serializer(
        name='FacilityState',
        fields={'states': drf_serializers.ListField(child=drf_serializers.CharField())}
    )}
)
class FacilityStatesView(APIView):
    """
    List all distinct states that have active facilities
    GET /api/facilities/states/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        states = (
            Facility.objects
            .filter(is_active=True)
            .exclude(state='')
            .values_list('state', flat=True)
            .distinct()
            .order_by('state')
        )
        return Response(list(states))


# ── History & Bookmark views ─────────────────────────────────────────────────

HISTORY_LIMIT = 50


@extend_schema(
    tags=["Facilities"],
    summary="Get recently viewed facilities",
    description=(
        "Returns the authenticated user's recently viewed facilities, "
        "most recent first. Limited to the last 50 unique facilities. "
        "Viewing the same facility again refreshes its position rather "
        "than creating a duplicate entry."
    ),
)
class FacilityViewHistoryListView(APIView):
    """
    GET    /api/facilities/history/   -> recent 50 unique facilities, most recent first
    DELETE /api/facilities/history/   -> clear all history for the user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (
            FacilityViewHistory.objects
            .filter(user=request.user)
            .select_related('facility')[:HISTORY_LIMIT]
        )
        serializer = FacilityViewHistorySerializer(qs, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    def delete(self, request):
        FacilityViewHistory.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FacilityViewRecordView(APIView):
    """
    POST   /api/facilities/:facility_id/view/   -> record/refresh a view
    DELETE /api/facilities/:facility_id/view/   -> remove single facility from history
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Facilities"],
        summary="Record a facility view",
        description="Records that the authenticated user viewed this facility. If already in their history, refreshes it to the top instead of duplicating.",
        responses={204: None, 404: None},
    )
    def post(self, request, facility_id):
        facility = Facility.objects.filter(pk=facility_id, is_active=True).first()
        if not facility:
            return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)

        FacilityViewHistory.objects.update_or_create(
            user=request.user,
            facility=facility,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Facilities"],
        summary="Remove a facility from view history",
        description="Removes this single facility from the authenticated user's view history.",
        responses={204: None, 404: None},
    )
    def delete(self, request, facility_id):
        deleted, _ = FacilityViewHistory.objects.filter(
            user=request.user, facility_id=facility_id
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Facilities"],
    summary="Get saved (bookmarked) facilities",
    description=(
        "Returns all facilities the authenticated user has saved, "
        "most recently saved first."
    ),
)
class FacilityBookmarkListView(APIView):
    """
    GET /api/facilities/bookmarks/   -> all saved facilities, most recent first
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (
            FacilityBookmark.objects
            .filter(user=request.user)
            .select_related('facility')
        )
        serializer = FacilityBookmarkSerializer(qs, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})


class FacilityBookmarkToggleView(APIView):
    """
    POST   /api/facilities/:facility_id/bookmark/   -> save
    DELETE /api/facilities/:facility_id/bookmark/   -> unsave
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Facilities"],
        summary="Save a facility",
        description="Bookmarks this facility for the authenticated user. Idempotent — calling this again on an already-saved facility returns 200 instead of creating a duplicate or erroring.",
        responses={201: None, 200: None, 404: None},
    )
    def post(self, request, facility_id):
        facility = Facility.objects.filter(pk=facility_id, is_active=True).first()
        if not facility:
            return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)

        bookmark, created = FacilityBookmark.objects.get_or_create(
            user=request.user, facility=facility
        )
        return Response(
            {'bookmarked': True},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Facilities"],
        summary="Remove a saved facility",
        description="Removes this facility from the authenticated user's bookmarks.",
        responses={204: None, 404: None},
    )
    def delete(self, request, facility_id):
        deleted, _ = FacilityBookmark.objects.filter(
            user=request.user, facility_id=facility_id
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
