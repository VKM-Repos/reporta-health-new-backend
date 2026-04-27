"""
Signals for User model
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Actions to perform after user is saved.
    Placeholder for welcome email — to be implemented with Celery.
    """
    if created:
        logger.info(f"New user registered: {instance.email}")