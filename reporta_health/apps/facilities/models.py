"""
Facility models with geospatial support
"""

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Facility(models.Model):
    """
    Health facility model with geospatial location
    """
    
    FACILITY_TYPES = [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('diagnostic', 'Diagnostic Center'),
        ('maternity', 'Maternity Home'),
        ('dental', 'Dental Clinic'),
        ('eye', 'Eye Clinic'),
        ('physiotherapy', 'Physiotherapy Center'),
        ('other', 'Other'),
    ]
    

    OWNERSHIP_TYPES = [
        ('federal_government', 'Federal Government'),
        ('state_government',   'State Government'),
        ('lga',                'Local Government (LGA)'),
        ('private',            'Private'),
        ('mission',            'Mission/Faith-based'),
        ('ngo',                'NGO'),
        ('other',              'Other'),
    ]

    CARE_LEVELS = [
        ('primary',   'Primary'),
        ('secondary', 'Secondary'),
        ('tertiary',  'Tertiary'),
        ('other',     'Other'),
    ]

    ownership = models.CharField(
        _('ownership type'),
        max_length=50,
        choices=OWNERSHIP_TYPES,
        default='private',
        db_index=True,
    )
    care_level = models.CharField(
        _('care level'),
        max_length=20,
        choices=CARE_LEVELS,
        default='primary',
        db_index=True,
    )

    # Basic Information
    name = models.CharField(_('facility name'), max_length=255, db_index=True)
    facility_type = models.CharField(
        _('facility type'),
        max_length=50,
        choices=FACILITY_TYPES,
        db_index=True
    )
    
    # Location
    address = models.TextField(_('address'))
    location = gis_models.PointField(
        _('location'),
        geography=True,
        srid=4326,
        help_text=_('Geospatial coordinates (longitude, latitude)')
    )
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    lga = models.CharField(
        _('local government area'),
        max_length=100,
        blank=True,
        db_index=True
    )

    operating_hours = models.JSONField(
        _('operating hours'),
        default=dict,
        blank=True,
        help_text=_('Structured weekly schedule')
    )
    # Contact Information
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Details
    description = models.TextField(_('description'), blank=True)
    services = models.TextField(
        _('services offered'),
        blank=True,
        help_text=_('Comma-separated list of services')
    )
    
    # Operating Hours (can be expanded to have separate model)
    monday_hours = models.CharField(_('Monday hours'), max_length=50, blank=True, default='9:00 AM - 5:00 PM')
    tuesday_hours = models.CharField(_('Tuesday hours'), max_length=50, blank=True, default='9:00 AM - 5:00 PM')
    wednesday_hours = models.CharField(_('Wednesday hours'), max_length=50, blank=True, default='9:00 AM - 5:00 PM')
    thursday_hours = models.CharField(_('Thursday hours'), max_length=50, blank=True, default='9:00 AM - 5:00 PM')
    friday_hours = models.CharField(_('Friday hours'), max_length=50, blank=True, default='9:00 AM - 5:00 PM')
    saturday_hours = models.CharField(_('Saturday hours'), max_length=50, blank=True, default='Closed')
    sunday_hours = models.CharField(_('Sunday hours'), max_length=50, blank=True, default='Closed')
    
    # Amenities
    has_parking = models.BooleanField(_('has parking'), default=False)
    has_wheelchair_access = models.BooleanField(_('wheelchair accessible'), default=False)
    has_emergency_service = models.BooleanField(_('has emergency service'), default=False)
    has_sarcs = models.BooleanField(
    _('has SARC'),
    default=False,
    help_text=_('Does this facility have a Sexual Assault Referral Centre unit?'),
    db_index=True,
)

    # Status & Ratings
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Has this facility been verified by admin?')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Is this facility currently operational?')
    )
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.IntegerField(_('total reviews'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('facility')
        verbose_name_plural = _('facilities')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['facility_type']),
            models.Index(fields=['is_verified', 'is_active']),
            models.Index(fields=['average_rating']),
            gis_models.Index(fields=['location']),  # Spatial index
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"
    
    @property
    def latitude(self):
        """Get latitude from Point"""
        return self.location.y if self.location else None
    
    @property
    def longitude(self):
        """Get longitude from Point"""
        return self.location.x if self.location else None


class FacilityImage(models.Model):
    """
    Images for facilities
    """
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('image'),
        upload_to='facilities/%Y/%m/%d/'
    )
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    is_primary = models.BooleanField(
        _('primary image'),
        default=False,
        help_text=_('Is this the main image for the facility?')
    )
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('facility image')
        verbose_name_plural = _('facility images')
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"Image for {self.facility.name}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset all other primary images
        if self.is_primary:
            FacilityImage.objects.filter(
                facility=self.facility,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class SARCProfile(models.Model):
    """
    Sexual Assault Referral Centre profile.
    Linked to a Facility — either a standalone SARC
    or a hospital with a SARC unit.
    """

    SERVICES = [
        ('medical', 'Medical Care'),
        ('counseling', 'Counseling & Psychosocial Support'),
        ('legal_aid', 'Legal Aid'),
        ('police_support', 'Police Support'),
        ('hiv_pep', 'HIV PEP'),
        ('emergency_contraception', 'Emergency Contraception'),
        ('shelter_referral', 'Shelter Referral'),
        ('court_support', 'Court Support & Accompaniment'),
        ('forensic', 'Forensic Medical Examination'),
        ('sti_testing', 'STI Testing & Treatment'),
    ]

    facility = models.OneToOneField(
        Facility,
        on_delete=models.CASCADE,
        related_name='sarc_profile',
    )
    unit_name = models.CharField(
        _('SARC unit name'),
        max_length=255,
        blank=True,
        help_text=_('Name of the SARC unit e.g. Hope Centre')
    )
    hotline_number = models.CharField(
        _('hotline number'),
        max_length=20,
        blank=True,
        help_text=_('24/7 crisis hotline number')
    )
    is_24_hours = models.BooleanField(_('24 hour service'), default=False)
    accepts_walk_ins = models.BooleanField(_('accepts walk-ins'), default=True)
    confidentiality_assured = models.BooleanField(
        _('confidentiality assured'), default=True
    )
    has_police_presence = models.BooleanField(_('has police presence'), default=False)
    has_legal_aid = models.BooleanField(_('has legal aid'), default=False)
    has_counseling = models.BooleanField(_('has counseling'), default=False)
    has_hiv_pep = models.BooleanField(_('has HIV PEP'), default=False)
    has_emergency_contraception = models.BooleanField(
        _('has emergency contraception'), default=False
    )
    has_shelter_referral = models.BooleanField(_('has shelter referral'), default=False)
    has_forensic = models.BooleanField(_('has forensic examination'), default=False)
    has_sti_testing = models.BooleanField(_('has STI testing'), default=False)
    has_court_support = models.BooleanField(_('has court support'), default=False)
    languages = models.JSONField(
        _('languages supported'),
        default=list,
        blank=True,
        help_text=_('List of languages spoken e.g. ["English", "Yoruba"]')
    )
    additional_info = models.TextField(_('additional information'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('SARC profile')
        verbose_name_plural = _('SARC profiles')

    def __str__(self):
        name = self.unit_name or self.facility.name
        return f"SARC: {name}"