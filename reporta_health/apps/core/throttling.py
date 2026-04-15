from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Strict throttle for login/register endpoints."""
    scope = 'auth'


class ReportCreateThrottle(UserRateThrottle):
    """Limit report submissions per user per day."""
    scope = 'report_create'


class ReviewCreateThrottle(UserRateThrottle):
    """Limit review submissions per user per day."""
    scope = 'review_create'