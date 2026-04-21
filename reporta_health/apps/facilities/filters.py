"""
Filters for Facility model
"""

import django_filters
from .models import Facility


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