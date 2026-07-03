"""
Review models for facilities
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Review(models.Model):
    """
    User reviews for facilities
    """
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    #body
    body = models.TextField(
     _  ('review text'),  
    )

    is_anonymous = models.BooleanField(
        _('anonymous'),
        default=False
    )

    is_published = models.BooleanField(
        _('published'),
        default=True
    )

    flag_count = models.PositiveIntegerField(
        _('flag count'),
        default=0
    )

    # Review content
    rating = models.IntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )
    visit_date = models.DateField(_('visit date'), blank=True, null=True)
    
    # Review status
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Has admin verified this review?')
    )
    helpful_count = models.IntegerField(_('helpful count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['facility', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-rating']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.facility.name} ({self.rating}★)"


class ReviewImage(models.Model):
    """
    Images attached to reviews
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('image'),
        upload_to='reviews/%Y/%m/%d/'
    )
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('review image')
        verbose_name_plural = _('review images')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Image for review by {self.review.user.get_full_name()}"