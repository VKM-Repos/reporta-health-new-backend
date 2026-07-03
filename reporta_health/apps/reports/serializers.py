"""
Serializers for Report models
"""

from rest_framework import serializers
from .models import FacilityReport, ReportImage
from apps.users.serializers import PublicUserSerializer


class ReportImageSerializer(serializers.ModelSerializer):
    """
    Serializer for report images
    """
    class Meta:
        model = ReportImage
        fields = ('id', 'image', 'caption', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class FacilityReportSerializer(serializers.ModelSerializer):
    """
    Serializer for facility reports
    """
    reporter = PublicUserSerializer(read_only=True)
    images = ReportImageSerializer(many=True, read_only=True)
    # changed: facility_name now falls back to the free-text field for ghost facility reports
    facility_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_facility_name(self, obj):
        if obj.facility:
            return obj.facility.name
        return obj.facility_name

    class Meta:
        model = FacilityReport
        fields = (
            'id',
            'facility',
            'facility_name',
            'reporter',
            'address',
            'city',
            'state',
            'phone_number',
            'reasons',
            'description',
            'is_anonymous',
            'status',
            'status_display',
            'admin_notes',
            'images',
            'created_at',
            'updated_at',
            'resolved_at',
        )
        read_only_fields = (
            'id',
            'reporter',
            'status',
            'admin_notes',
            'created_at',
            'updated_at',
            'resolved_at'
        )

    def create(self, validated_data):
        """
        Set reporter from request
        """
        request = self.context.get('request')
        validated_data['reporter'] = request.user
        return super().create(validated_data)


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating reports.
    Accepts either an existing `facility` FK, or free-text facility details
    for facilities not yet in the database (ghost facility reports).
    """
    class Meta:
        model = FacilityReport
        fields = (
            'facility', 'facility_name', 'address', 'city', 'state',
            'phone_number', 'reasons', 'description', 'is_anonymous',
        )
        extra_kwargs = {
            'facility': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        # added: require either an existing facility OR a facility_name for ghost reports
        if not data.get('facility') and not data.get('facility_name'):
            raise serializers.ValidationError(
                'Either select an existing facility or provide a facility name.'
            )
        if not data.get('reasons'):
            raise serializers.ValidationError('At least one reason must be selected.')
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reporter'] = request.user
        return super().create(validated_data)


class ReportStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating report status (admin only)
    """
    class Meta:
        model = FacilityReport
        fields = ('status', 'admin_notes', 'resolved_at')
    
    def validate_status(self, value):
        """
        Set resolved_at when status changes to resolved
        """
        if value == 'resolved' and not self.instance.resolved_at:
            from django.utils import timezone
            self.instance.resolved_at = timezone.now()
        return value