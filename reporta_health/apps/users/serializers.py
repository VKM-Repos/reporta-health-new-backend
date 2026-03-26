"""
Serializers for User model and authentication
"""

from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from .models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for user registration
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password', 'phone_number')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'phone_number',
            'profile_picture',
            'bio',
            'is_verified',
            'review_count',
            'date_joined',
        )
        read_only_fields = ('id', 'email', 'is_verified', 'date_joined')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'profile_picture', 'bio')


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer for public user information (shown in reviews, etc.)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'full_name', 'profile_picture', 'date_joined')