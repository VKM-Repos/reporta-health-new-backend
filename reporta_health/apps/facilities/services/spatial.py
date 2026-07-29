"""
Spatial helpers for facility clustering.
Handles bbox parsing, common filters, and PostGIS function definitions.
"""
from django.contrib.gis.geos import Polygon
from django.db.models import FloatField, Func


class ST_Y(Func):
    function = "ST_Y"
    template = "%(function)s(%(expressions)s::geometry)"
    output_field = FloatField()


class ST_X(Func):
    function = "ST_X"
    template = "%(function)s(%(expressions)s::geometry)"
    output_field = FloatField()


def parse_bbox(bbox_str: str):
    """Parse 'min_lng,min_lat,max_lng,max_lat' → Polygon or None."""
    try:
        parts = [float(v) for v in bbox_str.split(",")]
        if len(parts) != 4:
            return None
        min_lng, min_lat, max_lng, max_lat = parts
        if not (-180 <= min_lng <= 180 and -180 <= max_lng <= 180):
            return None
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            return None
        if min_lng >= max_lng or min_lat >= max_lat:
            return None
        poly = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        poly.srid = 4326
        return poly
    except (ValueError, TypeError):
        return None


def apply_common_filters(qs, params):
    """Apply shared optional filters to any queryset."""
    facility_type = params.get("facility_type")
    if facility_type:
        qs = qs.filter(facility_type=facility_type)

    state = params.get("state")
    if state:
        qs = qs.filter(state__iexact=state)

    has_sarcs = params.get("has_sarcs")
    if has_sarcs in ("true", "1"):
        qs = qs.filter(has_sarcs=True)

    has_fistula = params.get("has_fistula_programme")
    if has_fistula in ("true", "1"):
        qs = qs.filter(has_fistula_programme=True)

    has_gbv_services = params.get("has_gbv_services")
    if has_gbv_services in ("true", "1"):
        qs = qs.filter(has_gbv_services=True)

    is_verified = params.get("is_verified")
    if is_verified in ("true", "1"):
        qs = qs.filter(is_verified=True)

    city = params.get("city")
    if city:
        qs = qs.filter(city__icontains=city)

    lga = params.get("lga")
    if lga:
        qs = qs.filter(lga__icontains=lga)

    ownership = params.get("ownership")
    if ownership:
        qs = qs.filter(ownership=ownership)

    care_level = params.get("care_level")
    if care_level:
        qs = qs.filter(care_level=care_level)

    min_rating = params.get("min_rating")
    if min_rating:
        qs = qs.filter(average_rating__gte=min_rating)

    max_rating = params.get("max_rating")
    if max_rating:
        qs = qs.filter(average_rating__lte=max_rating)

    has_parking = params.get("has_parking")
    if has_parking in ("true", "1"):
        qs = qs.filter(has_parking=True)

    has_wheelchair_access = params.get("has_wheelchair_access")
    if has_wheelchair_access in ("true", "1"):
        qs = qs.filter(has_wheelchair_access=True)

    has_emergency_service = params.get("has_emergency_service")
    if has_emergency_service in ("true", "1"):
        qs = qs.filter(has_emergency_service=True)

    gbv_service_type = params.get("gbv_service_type")
    if gbv_service_type:
        types = [t.strip() for t in gbv_service_type.split(",")]
        qs = qs.filter(gbv_profile__service_types__overlap=types)

    return qs


def density_level(count: int) -> str:
    if count >= 700:
        return "high"
    if count >= 400:
        return "medium"
    return "low"