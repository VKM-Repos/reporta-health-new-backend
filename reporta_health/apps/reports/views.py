"""
Views for facility reports
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import FacilityReport, ReportImage
from .serializers import (
    FacilityReportSerializer,
    ReportCreateSerializer,
    ReportStatusUpdateSerializer,
    ReportImageSerializer
)
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from apps.core.throttling import ReportCreateThrottle

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

class ReportCreateView(generics.CreateAPIView):
    """
    Submit a report for a facility
    POST /api/reports/
    """
    queryset = FacilityReport.objects.all()
    serializer_class = ReportCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReportCreateThrottle]
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class ReportListView(generics.ListAPIView):
    """
    List all reports (admin only)
    GET /api/reports/
    
    Query parameters:
    - status: Filter by status (pending, investigating, resolved, rejected)
    - facility: Filter by facility ID
    """
    queryset = FacilityReport.objects.all().select_related(
        'facility', 'reporter'
    ).prefetch_related('images')
    serializer_class = FacilityReportSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reason', 'facility']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']


class ReportDetailView(generics.RetrieveAPIView):
    """
    Get report details (admin only)
    GET /api/reports/:id/
    """
    queryset = FacilityReport.objects.all().select_related(
        'facility', 'reporter'
    ).prefetch_related('images')
    serializer_class = FacilityReportSerializer
    permission_classes = [permissions.IsAdminUser]


class ReportStatusUpdateView(generics.UpdateAPIView):
    """
    Update report status (admin only)
    PATCH /api/reports/:id/status/
    """
    queryset = FacilityReport.objects.all()
    serializer_class = ReportStatusUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full report details after update
        return Response(
            FacilityReportSerializer(instance, context={'request': request}).data
        )


class ReportImageUploadView(generics.CreateAPIView):
    """
    Upload evidence image for a report
    POST /api/reports/:report_id/images/
    """
    serializer_class = ReportImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        report_id = self.kwargs.get('report_id')
        report = FacilityReport.objects.get(id=report_id)
        
        # Check if user is the reporter
        if report.reporter != self.request.user:
            raise permissions.PermissionDenied(
                "You can only upload images to your own reports."
            )
        
        serializer.save(report=report)


class UserReportsView(generics.ListAPIView):
    """
    Get reports submitted by current user
    GET /api/reports/my-reports/
    """
    serializer_class = FacilityReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FacilityReport.objects.filter(
            reporter=self.request.user
        ).select_related('facility').prefetch_related('images')