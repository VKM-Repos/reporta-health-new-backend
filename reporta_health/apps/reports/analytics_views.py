"""
Analytics / statistics views for report data.
"""

from __future__ import annotations

from django.core.cache import cache
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FacilityReport

CACHE_TTL = 60 * 15  # 15 minutes

REASON_MAP = dict(FacilityReport.REPORT_REASONS)


class ReportStatsByReasonView(APIView):
    """
    GET /api/reports/stats/by-reason/
    """
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        tags=["Report Analytics"],
        summary="Report counts grouped by reason",
    )
    def get(self, request):
        cache_key = "stats:reports:by_reason"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        rows = (
            FacilityReport.objects
            .values('reason')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        data = [
            {
                'reason': r['reason'],
                'reason_label': REASON_MAP.get(r['reason'], r['reason']),
                'count': r['count'],
            }
            for r in rows
        ]

        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


class ReportStatsByFacilityTypeView(APIView):
    """
    GET /api/reports/stats/by-facility-type/
    """
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        tags=["Report Analytics"],
        summary="Report counts grouped by facility type",
    )
    def get(self, request):
        cache_key = "stats:reports:by_facility_type"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        rows = (
            FacilityReport.objects
            .values('facility__facility_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        from apps.facilities.models import Facility
        facility_type_map = dict(Facility.FACILITY_TYPES)

        data = [
            {
                'facility_type': r['facility__facility_type'],
                'facility_type_label': facility_type_map.get(
                    r['facility__facility_type'], r['facility__facility_type']
                ),
                'count': r['count'],
            }
            for r in rows
        ]

        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


class ReportStatsByStateView(APIView):
    """
    GET /api/reports/stats/by-state/
    """
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        tags=["Report Analytics"],
        summary="Report counts grouped by state",
    )
    def get(self, request):
        cache_key = "stats:reports:by_state"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        rows = (
            FacilityReport.objects
            .values('facility__state')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        data = [
            {
                'state': r['facility__state'],
                'count': r['count'],
            }
            for r in rows
            if r['facility__state']
        ]

        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)