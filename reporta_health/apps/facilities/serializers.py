"""
Serializers for Facility models
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Facility, FacilityImage
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


class FacilityImageSerializer(serializers.ModelSerializer):
    """
    Serializer for facility images
    """
    class Meta:
        model = FacilityImage
        fields = ('id', 'image', 'caption', 'is_primary', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class FacilityListSerializer(serializers.ModelSerializer):
    """
    Serializer for facility list view (lightweight)
    """
    distance = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = (
            'id',
            'name',
            'facility_type',
            'address',
            'city',
            'state',
            'location',
            'phone_number',
            'average_rating',
            'total_reviews',
            'is_verified',
            'distance',
            'primary_image',
        )
    
    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_distance(self, obj):
        """Get distance from user location if available"""
        if hasattr(obj, 'distance'):
            return round(obj.distance.m, 2)  # Distance in meters
        return None
    
    @extend_schema_field(OpenApiTypes.URI)
    def get_primary_image(self, obj):
        """Get primary image URL"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary.image.url)
        return None
    
    @extend_schema_field({
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "format": "float"},
            "longitude": {"type": "number", "format": "float"},
        }
    })
    def get_location(self, obj):
        """Return location as lat/lng dict"""
        if obj.location:
            return {
                'latitude': obj.location.y,
                'longitude': obj.location.x
            }
        return None


class FacilityDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single facility view
    """
    images = FacilityImageSerializer(many=True, read_only=True)
    distance = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    operating_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = (
            'id',
            'name',
            'facility_type',
            'address',
            'city',
            'state',
            'location',
            'phone_number',
            'email',
            'website',
            'description',
            'services',
            'operating_hours',
            'has_parking',
            'has_wheelchair_access',
            'has_emergency_service',
            'is_verified',
            'is_active',
            'average_rating',
            'total_reviews',
            'images',
            'distance',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('average_rating', 'total_reviews', 'created_at', 'updated_at')
    
    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_distance(self, obj):
        """Get distance from user location if available"""
        if hasattr(obj, 'distance'):
            return round(obj.distance.m, 2)  # Distance in meters
        return None
    
    @extend_schema_field({
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "format": "float"},
            "longitude": {"type": "number", "format": "float"},
        }
    })
    def get_location(self, obj):
        """Return location as lat/lng dict"""
        if obj.location:
            return {
                'latitude': obj.location.y,
                'longitude': obj.location.x
            }
        return None
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_operating_hours(self, obj):
        """Return operating hours as structured dict"""
        return {
            'monday': obj.monday_hours,
            'tuesday': obj.tuesday_hours,
            'wednesday': obj.wednesday_hours,
            'thursday': obj.thursday_hours,
            'friday': obj.friday_hours,
            'saturday': obj.saturday_hours,
            'sunday': obj.sunday_hours,
        }


class FacilityCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a facility
    """
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    
    class Meta:
        model = Facility
        fields = (
            'name',
            'facility_type',
            'address',
            'city',
            'state',
            'latitude',
            'longitude',
            'phone_number',
            'email',
            'website',
            'description',
            'services',
            'monday_hours',
            'tuesday_hours',
            'wednesday_hours',
            'thursday_hours',
            'friday_hours',
            'saturday_hours',
            'sunday_hours',
            'has_parking',
            'has_wheelchair_access',
            'has_emergency_service',
        )
    
    def create(self, validated_data):
        # Extract lat/lng and create Point
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['location'] = Point(longitude, latitude, srid=4326)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Handle lat/lng update
        if 'latitude' in validated_data and 'longitude' in validated_data:
            latitude = validated_data.pop('latitude')
            longitude = validated_data.pop('longitude')
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        
        return super().update(instance, validated_data)