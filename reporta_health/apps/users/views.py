"""
Views for user profile and related endpoints
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, UserUpdateSerializer
from rest_framework.views import APIView
from .serializers import VerifyOTPSerializer, ResendOTPSerializer
from .emails import send_otp_email

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.throttling import AuthRateThrottle
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer


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
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        return Review.objects.filter(user=self.request.user).select_related('facility')
    
    def get_serializer_class(self):
        return ReviewSerializer

class VerifyOTPView(APIView):
    """
    Verify signup OTP code and activate the account.
    POST /api/users/verify-otp/
    Body: {"email": "...", "code": "123456"}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        user.is_active = True
        user.is_verified = True
        user.otp_code = None
        user.otp_created_at = None
        user.save(update_fields=['is_active', 'is_verified', 'otp_code', 'otp_created_at'])

        return Response({'detail': 'Account verified successfully.'}, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """
    Resend OTP code (rate-limited to 1 per 60 seconds).
    POST /api/users/resend-otp/
    Body: {"email": "..."}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        user.generate_otp()
        send_otp_email(user)

        return Response({'detail': 'A new code has been sent.'}, status=status.HTTP_200_OK)
