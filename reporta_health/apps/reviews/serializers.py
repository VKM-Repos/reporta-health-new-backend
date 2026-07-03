"""
Serializers for Review models
"""

from rest_framework import serializers
from .models import Review, ReviewImage
from apps.users.serializers import PublicUserSerializer


class ReviewImageSerializer(serializers.ModelSerializer):
    """
    Serializer for review images
    """
    class Meta:
        model = ReviewImage
        fields = ('id', 'image', 'caption', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews with user info
    """
    user = PublicUserSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    
    class Meta:
        model = Review
        fields = (
            'id',
            'facility',
            'facility_name',
            'user',
            'rating',
            'body',
            'is_anonymous',
            'is_published',   
            'flag_count',
            'visit_date',
            'is_verified',
            'helpful_count',
            'images',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'helpful_count','flag_count', 'is_published', 'is_verified', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Set user from request. Multiple reviews allowed — UI shows latest only.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating reviews
    """
    class Meta:
        model = Review
        fields = ('facility', 'rating', 'body', 'is_anonymous', 'visit_date')
    
    def create(self, validated_data):
        # Multiple reviews allowed per user per facility — UI shows latest only
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)