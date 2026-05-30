"""
Cache helpers for facility clustering.
"""
import hashlib

from django.core.cache import cache

from apps.facilities.utils.constants import CACHE_TIMEOUT_NEARBY, CACHE_TIMEOUT_BROWSE


def build_cache_key(params) -> str:
    """Build a cache key from request params, rounding bbox to 2dp for reuse."""
    bbox = params.get('bbox', '')
    if bbox:
        try:
            parts = [round(float(v), 2) for v in bbox.split(',')]
            bbox = ','.join(str(p) for p in parts)
        except (ValueError, TypeError):
            pass

    raw = (
        f"clusters"
        f":{bbox}"
        f":{params.get('zoom', '')}"
        f":{params.get('lat', '')}"
        f":{params.get('lng', '')}"
        f":{params.get('radius_km', '')}"
        f":{params.get('facility_type', '')}"
        f":{params.get('state', '')}"
        f":{params.get('has_sarcs', '')}"
        f":{params.get('has_fistula_programme', '')}"
        f":{params.get('is_verified', '')}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(params):
    """Return cached response or None."""
    return cache.get(build_cache_key(params))


def set_cache(params, data, nearby: bool = False):
    """Cache response data with appropriate timeout."""
    timeout = CACHE_TIMEOUT_NEARBY if nearby else CACHE_TIMEOUT_BROWSE
    cache.set(build_cache_key(params), data, timeout=timeout)