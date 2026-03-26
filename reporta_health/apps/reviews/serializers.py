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
            'title',
            'comment',
            'visit_date',
            'is_verified',
            'helpful_count',
            'images',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'helpful_count', 'is_verified', 'created_at', 'updated_at')
    
    def validate(self, data):
        """
        Validate that user hasn't already reviewed this facility
        """
        request = self.context.get('request')
        facility = data.get('facility')
        
        if request and facility:
            # Check for existing review (only on create, not update)
            if not self.instance:
                existing_review = Review.objects.filter(
                    user=request.user,
                    facility=facility
                ).exists()
                
                if existing_review:
                    raise serializers.ValidationError(
                        "You have already reviewed this facility."
                    )
        
        return data
    
    def create(self, validated_data):
        """
        Set user from request
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
        fields = ('facility', 'rating', 'title', 'comment', 'visit_date')
    
    def validate(self, data):
        """
        Validate that user hasn't already reviewed this facility
        """
        request = self.context.get('request')
        facility = data.get('facility')
        
        if request and facility:
            existing_review = Review.objects.filter(
                user=request.user,
                facility=facility
            ).exists()
            
            if existing_review:
                raise serializers.ValidationError(
                    "You have already reviewed this facility. You can edit your existing review instead."
                )
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)