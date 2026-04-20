"""
Analytics / statistics views for health facility data.

All views perform pure-DB aggregation (values + annotate) — no
Python-side grouping.  Results are cached with Django's cache
framework (15-minute TTL) since these are expensive GROUP BY
queries over potentially large datasets.
"""

from __future__ import annotations

from django.core.cache import cache
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Facility
from .serializers import (
    LGAStatsSerializer,
    StateCareLevelStatsSerializer,
    StateOwnershipStatsSerializer,
    StateStatsSerializer,
)

# ── helpers ──────────────────────────────────────────────────────────────────

FACILITY_TYPE_MAP = dict(Facility.FACILITY_TYPES)
OWNERSHIP_MAP     = dict(Facility.OWNERSHIP_TYPES)
CARE_LEVEL_MAP    = dict(Facility.CARE_LEVELS)

CACHE_TTL = 60 * 15  # 15 minutes


def _type_breakdown(qs) -> list[dict]:
    """
    Given a queryset already filtered to a state/LGA, return a
    list of {facility_type, facility_type_label, count} dicts.
    """
    rows = (
        qs.values("facility_type")
          .annotate(count=Count("id"))
          .order_by("-count")
    )
    return [
        {
            "facility_type":       r["facility_type"],
            "facility_type_label": FACILITY_TYPE_MAP.get(r["facility_type"], r["facility_type"]),
            "count":               r["count"],
        }
        for r in rows
    ]


def _ownership_breakdown(qs) -> list[dict]:
    rows = (
        qs.values("ownership")
          .annotate(count=Count("id"))
          .order_by("-count")
    )
    return [
        {
            "ownership":       r["ownership"],
            "ownership_label": OWNERSHIP_MAP.get(r["ownership"], r["ownership"]),
            "count":           r["count"],
        }
        for r in rows
    ]


def _care_level_breakdown(qs) -> list[dict]:
    rows = (
        qs.values("care_level")
          .annotate(count=Count("id"))
          .order_by("-count")
    )
    return [
        {
            "care_level":       r["care_level"],
            "care_level_label": CARE_LEVEL_MAP.get(r["care_level"], r["care_level"]),
            "count":            r["count"],
        }
        for r in rows
    ]


# ── base queryset ─────────────────────────────────────────────────────────────

def _active_qs():
    return Facility.objects.filter(is_active=True)


# ── views ─────────────────────────────────────────────────────────────────────

@extend_schema(
    tags=["Analytics"],
    summary="Facility counts across all states",
    description=(
        "Returns total facility count and per-facility-type breakdown "
        "for every state.  Results are cached for 15 minutes."
    ),
    responses={200: StateStatsSerializer(many=True)},
)
class FacilityStatsByAllStatesView(APIView):
    """
    GET /api/facilities/stats/by-state/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cache_key = "stats:facilities:all_states"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        base = _active_qs()

        # One query: state + facility_type counts
        rows = (
            base.exclude(Q(state="") | Q(state__isnull=True))
                .values("state", "facility_type")
                .annotate(count=Count("id"))
                .order_by("state", "-count")
        )

        # Group in Python — we already paid for the DB round-trip
        state_map: dict[str, dict] = {}
        for row in rows:
            s = row["state"]
            if s not in state_map:
                state_map[s] = {"state": s, "total": 0, "breakdown": []}
            state_map[s]["total"] += row["count"]
            state_map[s]["breakdown"].append(
                {
                    "facility_type":       row["facility_type"],
                    "facility_type_label": FACILITY_TYPE_MAP.get(
                        row["facility_type"], row["facility_type"]
                    ),
                    "count": row["count"],
                }
            )

        data = sorted(state_map.values(), key=lambda x: x["state"])
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


@extend_schema(
    tags=["Analytics"],
    summary="Facility counts for a single state",
    description="Returns total and per-facility-type breakdown for the given state name.",
    parameters=[
        OpenApiParameter(
            "state",
            OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="State name (e.g. Lagos, Abuja)",
        )
    ],
    responses={200: StateStatsSerializer},
)
class FacilityStatsByStateView(APIView):
    """
    GET /api/facilities/stats/by-state/<state>/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, state: str):
        # Normalise: "lagos" → "Lagos" for consistent lookup
        state_name = state.strip().title()
        cache_key = f"stats:facilities:state:{state_name.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = _active_qs().filter(state__iexact=state_name)
        total = qs.count()

        if total == 0:
            return Response(
                {"detail": f"No active facilities found for state '{state_name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "state":     state_name,
            "total":     total,
            "breakdown": _type_breakdown(qs),
        }
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


@extend_schema(
    tags=["Analytics"],
    summary="Facility counts by ownership type for a state",
    parameters=[
        OpenApiParameter(
            "state",
            OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="State name",
        )
    ],
    responses={200: StateOwnershipStatsSerializer},
)
class FacilityStatsByStateOwnershipView(APIView):
    """
    GET /api/facilities/stats/by-state/<state>/ownership/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, state: str):
        state_name = state.strip().title()
        cache_key = f"stats:facilities:state:{state_name.lower()}:ownership"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = _active_qs().filter(state__iexact=state_name)
        total = qs.count()

        if total == 0:
            return Response(
                {"detail": f"No active facilities found for state '{state_name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "state":     state_name,
            "total":     total,
            "breakdown": _ownership_breakdown(qs),
        }
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


@extend_schema(
    tags=["Analytics"],
    summary="Facility counts by care level for a state",
    parameters=[
        OpenApiParameter(
            "state",
            OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="State name",
        )
    ],
    responses={200: StateCareLevelStatsSerializer},
)
class FacilityStatsByStateCareLevelView(APIView):
    """
    GET /api/facilities/stats/by-state/<state>/care-level/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, state: str):
        state_name = state.strip().title()
        cache_key = f"stats:facilities:state:{state_name.lower()}:care_level"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = _active_qs().filter(state__iexact=state_name)
        total = qs.count()

        if total == 0:
            return Response(
                {"detail": f"No active facilities found for state '{state_name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "state":     state_name,
            "total":     total,
            "breakdown": _care_level_breakdown(qs),
        }
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


@extend_schema(
    tags=["Analytics"],
    summary="Facility counts across all LGAs",
    description=(
        "Returns total and per-facility-type breakdown for every LGA. "
        "Each entry includes the parent state name.  Cached for 15 minutes."
    ),
    responses={200: LGAStatsSerializer(many=True)},
)
class FacilityStatsByAllLGAsView(APIView):
    """
    GET /api/facilities/stats/by-lga/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cache_key = "stats:facilities:all_lgas"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        base = _active_qs()

        rows = (
            base.exclude(Q(lga="") | Q(lga__isnull=True))
                .values("lga", "state", "facility_type")
                .annotate(count=Count("id"))
                .order_by("lga", "-count")
        )

        lga_map: dict[str, dict] = {}
        for row in rows:
            key = f"{row['lga']}|{row['state']}"
            if key not in lga_map:
                lga_map[key] = {
                    "lga":       row["lga"],
                    "state":     row["state"],
                    "total":     0,
                    "breakdown": [],
                }
            lga_map[key]["total"] += row["count"]
            lga_map[key]["breakdown"].append(
                {
                    "facility_type":       row["facility_type"],
                    "facility_type_label": FACILITY_TYPE_MAP.get(
                        row["facility_type"], row["facility_type"]
                    ),
                    "count": row["count"],
                }
            )

        data = sorted(lga_map.values(), key=lambda x: (x["state"], x["lga"]))
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)


@extend_schema(
    tags=["Analytics"],
    summary="Facility counts for a single LGA",
    description="Returns total and per-facility-type breakdown for the given LGA name.",
    parameters=[
        OpenApiParameter(
            "lga",
            OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="LGA name (e.g. Ikeja, Eti-Osa)",
        )
    ],
    responses={200: LGAStatsSerializer},
)
class FacilityStatsByLGAView(APIView):
    """
    GET /api/facilities/stats/by-lga/<lga>/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, lga: str):
        lga_name = lga.strip().title()
        cache_key = f"stats:facilities:lga:{lga_name.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = _active_qs().filter(lga__iexact=lga_name)
        total = qs.count()

        if total == 0:
            return Response(
                {"detail": f"No active facilities found for LGA '{lga_name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Grab the parent state from the first matching record
        first = qs.values("state").first()
        state_name = first["state"] if first else ""

        data = {
            "lga":       lga_name,
            "state":     state_name,
            "total":     total,
            "breakdown": _type_breakdown(qs),
        }
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)