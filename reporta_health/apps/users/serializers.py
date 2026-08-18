"""
Serializers for User model and authentication
"""

from rest_framework import serializers
from djoser.serializers import UserCreatePasswordRetypeSerializer as BaseUserCreateSerializer
from .models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for user registration
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 'password')

    def create(self, validated_data):
        user = super().create(validated_data)
        user.is_active = False
        user.save(update_fields=['is_active'])
        user.generate_otp()
        # SMTP is not fully configured yet — sending here was blocking the
        # request for 2+ minutes and killing gunicorn workers (502s).
        # Re-enable once email is properly set up, ideally via an async
        # task (Celery/Django-Q) rather than synchronously in the request.
        # from .emails import send_otp_email
        # send_otp_email(user)
        import logging
        logging.getLogger(__name__).info(
            "OTP generated (email disabled)",
            extra={"user_id": user.pk, "email": user.email, "otp_code": user.otp_code},
        )
        return user



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

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No user found with this email.'})

        if user.is_verified:
            raise serializers.ValidationError({'email': 'This account is already verified.'})

        if not user.is_otp_valid(attrs['code']):
            raise serializers.ValidationError({'code': 'Invalid or expired code.'})

        attrs['user'] = user
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No user found with this email.'})

        if user.is_verified:
            raise serializers.ValidationError({'email': 'This account is already verified.'})

        wait = user.seconds_until_otp_resend_allowed()
        if wait > 0:
            raise serializers.ValidationError({'email': f'Please wait {wait} seconds before requesting a new code.'})

        attrs['user'] = user
        return attrs
