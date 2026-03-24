"""
Signals for User model
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Actions to perform after user is saved
    """
    if created:
        # Send welcome email or create user profile
        # Can add Celery task here for async email sending
        pass