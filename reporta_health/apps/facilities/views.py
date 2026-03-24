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
from .models import Facility, FacilityImage
from .serializers import (
    FacilityListSerializer,
    FacilityDetailSerializer,
    FacilityCreateSerializer,
    FacilityImageSerializer
)
from .filters import FacilityFilter


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
    queryset = Facility.objects.filter(is_active=True).prefetch_related('images')
    serializer_class = FacilityListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FacilityFilter
    search_fields = ['name', 'description', 'services', 'address']
    ordering_fields = ['name', 'average_rating', 'created_at', 'total_reviews']
    ordering = ['-average_rating']


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
    
    # Get search radius (default 5km)
    try:
        radius = int(request.query_params.get('radius', 5000))
    except ValueError:
        radius = 5000
    
    # Create user location point
    user_location = Point(longitude, latitude, srid=4326)
    
    # Query facilities within radius
    queryset = Facility.objects.filter(
        is_active=True,
        location__distance_lte=(user_location, D(m=radius))
    ).annotate(
        distance=Distance('location', user_location)
    ).order_by('distance')
    
    # Apply facility type filter if provided
    facility_type = request.query_params.get('facility_type')
    if facility_type:
        queryset = queryset.filter(facility_type=facility_type)
    
    # Apply limit
    limit = int(request.query_params.get('limit', 20))
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
    queryset = Facility.objects.filter(is_active=True).prefetch_related('images', 'reviews')
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
        serializer.save(facility_id=facility_id)