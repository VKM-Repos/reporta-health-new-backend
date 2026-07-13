"""
Serializers for Facility models
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Facility, FacilityImage, FacilityViewHistory, FacilityBookmark, GBVServiceProfile, SARCProfile
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


class GBVServiceProfileSerializer(serializers.ModelSerializer):
    """
    Nested serializer for GBV service profile.
    Used inside FacilityDetailSerializer.
    """
    class Meta:
        model = GBVServiceProfile
        fields = (
            'service_types',
            'target_group',
            'organisation_type',
            'contact_person',
            'accessibility_info',
            'services_detail',
        )


class SARCProfileInlineSerializer(serializers.ModelSerializer):
    """
    Nested serializer for SARC profile.
    Used inside FacilityDetailSerializer.
    """
    class Meta:
        model = SARCProfile
        fields = (
            'unit_name',
            'hotline_number',
            'has_counseling',
            'has_legal_aid',
            'has_hiv_pep',
            'has_forensic',
            'has_sti_testing',
            'has_shelter_referral',
            'has_emergency_contraception',
            'additional_info',
        )


class FacilityListSerializer(serializers.ModelSerializer):
    """
    Serializer for facility list view (lightweight)
    """
    distance = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    gbv_profile = GBVServiceProfileSerializer(read_only=True)
    sarc_profile = SARCProfileInlineSerializer(read_only=True)
    
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
            'has_sarcs',
            'has_fistula_programme',
            'has_gbv_services',
            'gbv_profile',   # added: nested GBV profile
            'sarc_profile',  # added: nested SARC profile
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
        images = obj.images.all()  # uses prefetch cache, no extra query
        primary = next((img for img in images if img.is_primary), None)
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
    gbv_profile = GBVServiceProfileSerializer(read_only=True)  # added: nested GBV profile
    sarc_profile = SARCProfileInlineSerializer(read_only=True)  # added: nested SARC profile
    
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
            'has_sarcs',
            'has_fistula_programme',
            'has_gbv_services',
            'gbv_profile',   # added: nested GBV profile
            'sarc_profile',  # added: nested SARC profile
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

        # apps/facilities/serializers.py

# ── Analytics serializers ────────────────────────────────────────────────────

class FacilityTypeCountSerializer(serializers.Serializer):
    """Single facility_type → count pair."""
    facility_type       = serializers.CharField()
    facility_type_label = serializers.CharField()
    count               = serializers.IntegerField()


class StateStatsSerializer(serializers.Serializer):
    """Per-state breakdown by facility_type."""
    state      = serializers.CharField()
    total      = serializers.IntegerField()
    breakdown  = FacilityTypeCountSerializer(many=True)


class LGAStatsSerializer(serializers.Serializer):
    """Per-LGA breakdown by facility_type."""
    lga       = serializers.CharField()
    state     = serializers.CharField()
    total     = serializers.IntegerField()
    breakdown = FacilityTypeCountSerializer(many=True)


class OwnershipCountSerializer(serializers.Serializer):
    ownership       = serializers.CharField()
    ownership_label = serializers.CharField()
    count           = serializers.IntegerField()


class CareLevelCountSerializer(serializers.Serializer):
    care_level       = serializers.CharField()
    care_level_label = serializers.CharField()
    count            = serializers.IntegerField()


class StateOwnershipStatsSerializer(serializers.Serializer):
    state     = serializers.CharField()
    total     = serializers.IntegerField()
    breakdown = OwnershipCountSerializer(many=True)


class StateCareLevelStatsSerializer(serializers.Serializer):
    state     = serializers.CharField()
    total     = serializers.IntegerField()
    breakdown = CareLevelCountSerializer(many=True)

# ── History & Bookmark serializers ───────────────────────────────────────────

class FacilityViewHistorySerializer(serializers.ModelSerializer):
    facility_id = serializers.IntegerField(source='facility.id', read_only=True)
    name = serializers.CharField(source='facility.name', read_only=True)
    facility_type = serializers.CharField(source='facility.facility_type', read_only=True)
    state = serializers.CharField(source='facility.state', read_only=True)
    lga = serializers.CharField(source='facility.lga', read_only=True)
    average_rating = serializers.DecimalField(
        source='facility.average_rating', max_digits=3, decimal_places=2, read_only=True
    )
    distance = serializers.SerializerMethodField()

    class Meta:
        model = FacilityViewHistory
        fields = ('facility_id', 'name', 'facility_type', 'state', 'lga', 'average_rating', 'distance', 'viewed_at')

    def get_distance(self, obj):
        """Distance from user location, only present if the view was annotated with it"""
        if hasattr(obj, 'distance') and obj.distance is not None:
            return round(obj.distance.m, 2)
        return None


class FacilityBookmarkSerializer(serializers.ModelSerializer):
    facility_id = serializers.IntegerField(source='facility.id', read_only=True)
    name = serializers.CharField(source='facility.name', read_only=True)
    facility_type = serializers.CharField(source='facility.facility_type', read_only=True)
    state = serializers.CharField(source='facility.state', read_only=True)
    lga = serializers.CharField(source='facility.lga', read_only=True)
    average_rating = serializers.DecimalField(
        source='facility.average_rating', max_digits=3, decimal_places=2, read_only=True
    )
    distance = serializers.SerializerMethodField()

    class Meta:
        model = FacilityBookmark
        fields = ('facility_id', 'name', 'facility_type', 'state', 'lga', 'average_rating', 'distance', 'created_at')

    def get_distance(self, obj):
        """Distance from user location, only present if the view was annotated with it"""
        if hasattr(obj, 'distance') and obj.distance is not None:
            return round(obj.distance.m, 2)
        return None
