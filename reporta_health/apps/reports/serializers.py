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
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FacilityReport
        fields = (
            'id',
            'facility',
            'facility_name',
            'reporter',
            'reason',
            'reason_display',
            'description',
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
    Simplified serializer for creating reports
    """
    class Meta:
        model = FacilityReport
        fields = ('facility', 'reason', 'description')
    
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