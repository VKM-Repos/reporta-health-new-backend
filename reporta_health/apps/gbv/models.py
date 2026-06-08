"""
Models for GBV (Gender Based Violence) services app.
"""
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GistIndex

class GBVService(models.Model):

    ORGANISATION_TYPES = [
        ('governmental',     'Governmental'),
        ('national_ngo',     'National NGO'),
        ('international_ngo','International NGO'),
        ('private',          'Private'),
        ('other',            'Other'),
    ]

    TARGET_GROUPS = [
        ('adults_and_children', 'Adults and Children'),
        ('adults_only',         'Adults Only (18 and Over)'),
        ('children_only',       'Children Only (Under 18)'),
    ]

    # Location
    state             = models.CharField(_('state'), max_length=100)
    lga               = models.CharField(_('LGA'), max_length=100, blank=True)

    # Identity
    name              = models.CharField(_('name'), max_length=255)
    organisation_type = models.CharField(
        _('organisation type'),
        max_length=50,
        choices=ORGANISATION_TYPES,
        default='governmental',
    )

    # Services
    services          = models.TextField(_('services offered'), blank=True)
    target_group      = models.CharField(
        _('target group'),
        max_length=50,
        choices=TARGET_GROUPS,
        default='adults_and_children',
    )

    # Contact
    address           = models.TextField(_('address'), blank=True)
    phone_number      = models.CharField(_('phone number'), max_length=100, blank=True)
    contact_person    = models.CharField(_('contact person'), max_length=255, blank=True)

    # Accessibility
    accessibility_info = models.TextField(_('accessibility info'), blank=True)
    operating_hours    = models.CharField(_('operating hours'), max_length=100, blank=True)

    # Geospatial
    location          = gis_models.PointField(
        _('location'),
        srid=4326,
        null=True,
        blank=True,
    )

    # Status
    is_active         = models.BooleanField(_('active'), default=True)

    # Timestamps
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('GBV service')
        verbose_name_plural = _('GBV services')
        ordering            = ['state', 'name']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['lga']),
            models.Index(fields=['organisation_type']),
            models.Index(fields=['is_active']),
            GistIndex(fields=['location']),
        ]

    def __str__(self):
        return f"{self.name} — {self.state}"