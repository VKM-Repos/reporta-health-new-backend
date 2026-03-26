"""
Report models for facilities
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class FacilityReport(models.Model):
    """
    User reports for facilities (fake facilities, wrong info, etc.)
    """
    
    REPORT_REASONS = [
        ('fake', 'Fake Facility'),
        ('closed', 'Permanently Closed'),
        ('wrong_info', 'Wrong Information'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate Entry'),
        ('spam', 'Spam'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    # Related objects
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facility_reports'
    )
    
    # Report details
    reason = models.CharField(
        _('reason'),
        max_length=20,
        choices=REPORT_REASONS
    )
    description = models.TextField(
        _('description'),
        help_text=_('Detailed explanation of the issue')
    )
    
    # Status tracking
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_notes = models.TextField(
        _('admin notes'),
        blank=True,
        help_text=_('Internal notes for admins')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('reported at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    resolved_at = models.DateTimeField(_('resolved at'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('facility report')
        verbose_name_plural = _('facility reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['facility', '-created_at']),
            models.Index(fields=['reporter', '-created_at']),
        ]
    
    def __str__(self):
        return f"Report: {self.facility.name} - {self.get_reason_display()}"


class ReportImage(models.Model):
    """
    Evidence images attached to reports
    """
    report = models.ForeignKey(
        FacilityReport,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('image'),
        upload_to='reports/%Y/%m/%d/'
    )
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('report image')
        verbose_name_plural = _('report images')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Evidence for report #{self.report.id}"