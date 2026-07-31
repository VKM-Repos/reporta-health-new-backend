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
        ('does_not_exist', 'Facility Does Not Exist'),
        ('wrong_info', 'Wrong or Misleading Information'),
        ('unsafe_conditions', 'Poor and Unsafe Conditions'),
        ('scam_fraud', 'Scam or Fraud'),
        ('unlicensed', 'Unlicensed or Unauthorized'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    # Related objects
    # added: nullable — null when reporting a facility not yet in the DB (ghost facility report)
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='reports',
        null=True,
        blank=True,
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facility_reports'
    )
    # added: free-text fields used when facility is null (ghost facility report)
    facility_name = models.CharField(_('facility name'), max_length=255, blank=True)
    address = models.CharField(_('address'), max_length=500, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    # added: report can select multiple reasons
    reasons = models.JSONField(_('reasons'), default=list, blank=True)
    # added: hides reporter identity in admin UI when true (reporter FK is still set for accountability)
    is_anonymous = models.BooleanField(_('reported anonymously'), default=False)
    
    # Report details
    reason = models.CharField(
        _('reason'),
        max_length=20,
        choices=REPORT_REASONS
    )
    # changed: now optional — screen labels this "Tell us more (optional)"
    description = models.TextField(
        _('description'),
        blank=True,
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
        facility_label = self.facility.name if self.facility_id else (self.facility_name or "(ghost facility)")
        return f"Report: {facility_label} - {self.get_reason_display()}"


def get_reports_storage():
    from config.settings.storage import ReportsStorage
    return ReportsStorage()

class ReportImage(models.Model):
    report = models.ForeignKey(
        FacilityReport,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('image'),
        storage=get_reports_storage,
        upload_to='%Y/%m/%d/'
    )
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)

    class Meta:
        verbose_name = _('report image')
        verbose_name_plural = _('report images')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Evidence for report #{self.report.id}"