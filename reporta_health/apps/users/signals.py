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
    if not created:
        return  # early return for readability

    logger.info(
        "New user registered",
        extra={
            "user_id": instance.pk,
            "email": instance.email,
        }
    )
    # TODO: send welcome email via Celery
    # send_welcome_email.delay(instance.pk)