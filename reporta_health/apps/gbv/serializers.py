"""
Serializers for GBV app.
"""
from rest_framework import serializers
from .models import GBVService


class GBVServiceSerializer(serializers.ModelSerializer):

    distance = serializers.SerializerMethodField()

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

    def get_distance(self, obj):
        if hasattr(obj, 'distance'):
            return round(obj.distance.m, 1)
        return None


class GBVNearbyResultSerializer(serializers.Serializer):
    """
    Combined serializer for the /gbv/nearby/ endpoint.
    Returns both GBV services and SARC facilities in one list.
    """
    kind          = serializers.CharField()   # 'gbv_service' or 'sarc'
    id            = serializers.IntegerField()
    name          = serializers.CharField()
    state         = serializers.CharField()
    lga           = serializers.CharField()
    address       = serializers.CharField()
    phone_number  = serializers.CharField()
    services      = serializers.CharField()
    distance_m    = serializers.FloatField()
    location      = serializers.DictField()
    extra         = serializers.DictField()   # kind-specific fields