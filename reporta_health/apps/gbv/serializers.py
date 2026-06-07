"""
Serializers for GBV app.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import GBVService


class GBVServiceSerializer(serializers.ModelSerializer):

    distance = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model  = GBVService
        fields = (
            'id',
            'name',
            'state',
            'lga',
            'organisation_type',
            'services',
            'target_group',
            'address',
            'phone_number',
            'contact_person',
            'accessibility_info',
            'operating_hours',
            'location',
            'is_active',
            'distance',
        )

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_distance(self, obj) -> float:
        if hasattr(obj, 'distance'):
            return round(obj.distance.m, 1)
        return None

    @extend_schema_field({'type': 'object', 'properties': {
        'latitude':  {'type': 'number'},
        'longitude': {'type': 'number'},
    }})
    def get_location(self, obj):
        if obj.location:
            return {
                'latitude':  obj.location.y,
                'longitude': obj.location.x,
            }
        return None


class GBVNearbyResultSerializer(serializers.Serializer):
    """
    Combined serializer for the /gbv/nearby/ endpoint.
    """
    kind          = serializers.CharField()
    id            = serializers.IntegerField()
    name          = serializers.CharField()
    state         = serializers.CharField()
    lga           = serializers.CharField()
    address       = serializers.CharField()
    phone_number  = serializers.CharField()
    services      = serializers.CharField()
    distance_m    = serializers.FloatField()
    location      = serializers.DictField()
    extra         = serializers.DictField()