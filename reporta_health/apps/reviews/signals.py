"""
Signals for Review model
Auto-update facility average rating when reviews change
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review


@receiver([post_save, post_delete], sender=Review)
def update_facility_rating(sender, instance, **kwargs):
    """
    Update facility average rating and total reviews when a review is added/updated/deleted
    """
    facility = instance.facility
    reviews = facility.reviews.all()
    
    # Calculate new average
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Update facility
    facility.average_rating = round(avg_rating, 2)
    facility.total_reviews = reviews.count()
    facility.save(update_fields=['average_rating', 'total_reviews'])