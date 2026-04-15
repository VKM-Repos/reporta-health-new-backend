"""
Views for reviews
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Review, ReviewImage
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewImageSerializer
from django.shortcuts import get_object_or_404
from apps.core.throttling import ReviewCreateThrottle

class FacilityReviewListView(generics.ListAPIView):
    """
    Get reviews for a specific facility
    GET /api/facilities/:facility_id/reviews/
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        facility_id = self.kwargs.get('facility_id')
        return Review.objects.filter(
            facility_id=facility_id
        ).select_related('user', 'facility').prefetch_related('images')


class ReviewCreateView(generics.CreateAPIView):
    """
    Create a review for a facility
    POST /api/facilities/:facility_id/reviews/
    """
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReviewCreateThrottle]

    
    def create(self, request, *args, **kwargs):
        # Add facility to request data
        data = request.data.copy()
        data['facility'] = self.kwargs.get('facility_id')
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return full review details
        review = serializer.instance
        return Response(
            ReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class ReviewDetailView(generics.RetrieveAPIView):
    """
    Get review details
    GET /api/reviews/:id/
    """
    queryset = Review.objects.all().select_related('user', 'facility').prefetch_related('images')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]


class ReviewUpdateView(generics.UpdateAPIView):
    """
    Update own review
    PUT/PATCH /api/reviews/:id/
    """
    queryset = Review.objects.all().select_related('user')
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You can only edit your own reviews.")
        return obj


class ReviewDeleteView(generics.DestroyAPIView):
    """
    Delete own review
    DELETE /api/reviews/:id/
    """
    queryset = Review.objects.all().select_related('user')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        return obj

class ReviewImageUploadView(generics.CreateAPIView):
    """
    Upload image for a review
    POST /api/reviews/:review_id/images/
    
    """
    serializer_class = ReviewImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        review_id = self.kwargs.get('review_id')
        # 1. Check if review exists → 404
        review = get_object_or_404(Review, id=review_id)
        # 2. Check ownership → 403
        if review.user != request.user:
            raise PermissionDenied("You can only upload images to your own reviews.")
        # 3. Now validate serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(review=review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
# Note: We can add image deletion endpoint later if needed, but for now users can just update their review to remove images.