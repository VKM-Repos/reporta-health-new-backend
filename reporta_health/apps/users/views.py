"""
Views for user profile and related endpoints
"""

from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, UserUpdateSerializer

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.throttling import AuthRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """JWT login with rate limiting."""
    throttle_classes = [AuthRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    """JWT refresh with rate limiting."""
    throttle_classes = [AuthRateThrottle]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get or update current authenticated user profile
    GET /api/users/me/
    PUT/PATCH /api/users/me/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


class UserReviewsView(generics.ListAPIView):
    """
    Get reviews submitted by current user
    GET /api/users/me/reviews/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from apps.reviews.models import Review
        return Review.objects.filter(user=self.request.user).select_related('facility')
    
    def get_serializer_class(self):
        from apps.reviews.serializers import ReviewSerializer
        return ReviewSerializer