"""
Custom User model for Reporta Health
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CaseInsensitiveUserManager(UserManager):
    """
    Default UserManager.get_by_natural_key() does a case-sensitive match on
    USERNAME_FIELD (email, here). That means a login with different
    capitalization than what's stored (e.g. Foo@Gmail.com vs foo@gmail.com)
    fails with 'No active account found' even with the correct password.
    Email addresses are conventionally treated case-insensitively, so this
    overrides the lookup to match on email__iexact instead.
    """
    def get_by_natural_key(self, username):
        case_insensitive_field = f"{self.model.USERNAME_FIELD}__iexact"
        return self.get(**{case_insensitive_field: username})


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    
    # Override email to make it required and unique

    username = models.CharField(max_length=150, unique=True)

    first_name = models.CharField(
        _('first name'),
        max_length=50,
        blank=True
    )

    last_name = models.CharField(
        _('last name'),
        max_length=50,
        blank=True
    )
    email = models.EmailField(_('email address'), unique=True)

    objects = CaseInsensitiveUserManager()
    
    # Additional fields
    phone_number = models.CharField(
        _('phone number'),
        max_length=150,
        blank=True,
        help_text=_('User phone number')
    )
    
    def get_avatars_storage():
        from config.settings.storage import AvatarsStorage
        return AvatarsStorage()

    profile_picture = models.ImageField(
        _('profile picture'),
        storage=get_avatars_storage,
        upload_to='',
        blank=True,
        null=True
    )
    bio = models.TextField(
        _('bio'),
        max_length=500,
        blank=True
    )
    
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether the user has verified their email.')
    )
    
    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Make email the login field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.email
    
    otp_code = models.CharField(
        _('otp code'),
        max_length=6,
        blank=True,
        null=True,
    )
    otp_created_at = models.DateTimeField(
        _('otp created at'),
        blank=True,
        null=True,
    )

    @property
    def review_count(self):
        """Return total number of reviews submitted by user"""
        return self.reviews.count()

    def generate_otp(self):
        """Generate a new 6-digit OTP, store it, and return the code."""
        import random
        from django.utils import timezone

        code = f"{random.randint(0, 999999):06d}"
        self.otp_code = code
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp_code', 'otp_created_at'])
        return code

    def is_otp_valid(self, code):
        """Check the given code matches and is within the 5-minute window."""
        from django.utils import timezone
        from datetime import timedelta

        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_code != code:
            return False
        if timezone.now() > self.otp_created_at + timedelta(minutes=5):
            return False
        return True

    def seconds_until_otp_resend_allowed(self):
        """Return seconds remaining before another OTP can be sent (rate limit: 1/min). 0 if allowed now."""
        from django.utils import timezone

        if not self.otp_created_at:
            return 0
        elapsed = (timezone.now() - self.otp_created_at).total_seconds()
        remaining = 60 - elapsed
        return max(0, int(remaining))