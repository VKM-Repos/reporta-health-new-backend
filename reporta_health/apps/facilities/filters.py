"""
Filters for Facility model
"""

import django_filters
from .models import Facility
from django.contrib.gis.geos import Polygon

class FacilityFilter(django_filters.FilterSet):
    """
    Filter for facilities with multiple criteria
    """
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    has_parking = django_filters.BooleanFilter()
    has_wheelchair_access = django_filters.BooleanFilter()
    has_emergency_service = django_filters.BooleanFilter()
    is_verified = django_filters.BooleanFilter()
    has_sarcs = django_filters.BooleanFilter()
    has_fistula_programme = django_filters.BooleanFilter()
    has_gbv_services = django_filters.BooleanFilter()
    gbv_service_type = django_filters.CharFilter(method="filter_gbv_service_type")
    

    min_lat = django_filters.NumberFilter(method='filter_bbox')
    max_lat = django_filters.NumberFilter(method='filter_bbox')
    min_lng = django_filters.NumberFilter(method='filter_bbox')
    max_lng = django_filters.NumberFilter(method='filter_bbox')

    def filter_gbv_service_type(self, queryset, name, value):
        types = [t.strip() for t in value.split(",")]
        for service_type in types:
            queryset = queryset.filter(gbv_profile__service_types__contains=[service_type])
        return queryset

    def filter_bbox(self, queryset, name, value):
        min_lat = self.data.get('min_lat')
        max_lat = self.data.get('max_lat')
        min_lng = self.data.get('min_lng')
        max_lng = self.data.get('max_lng')

        if all([min_lat, max_lat, min_lng, max_lng]):
            bbox = Polygon.from_bbox((
                float(min_lng), float(min_lat),
                float(max_lng), float(max_lat)
            ))
            bbox.srid = 4326
            return queryset.filter(location__within=bbox)
        return queryset

    class Meta:
        model = Facility
        fields = {
            'facility_type': ['exact'],
            'city': ['exact', 'icontains'],
            'state': ['exact', 'icontains'],
            'lga': ['exact', 'icontains'],    
            'ownership': ['exact'],            
            'care_level': ['exact'], 
        }  