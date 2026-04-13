"""
Admin configuration for Facility models
"""

from django.contrib.gis import admin
from .models import Facility, FacilityImage
from leaflet.admin import LeafletGeoAdmin

class FacilityImageInline(admin.TabularInline):
    """
    Inline admin for facility images
    """
    model = FacilityImage
    extra = 1
    fields = ('image', 'caption', 'is_primary')


@admin.register(Facility)
class FacilityAdmin(LeafletGeoAdmin):
    """
    Admin for Facility model with map widget
    """
    list_display = (
        'name',
        'facility_type',
        'city',
        'state',
        'is_verified',
        'is_active',
        'average_rating',
        'total_reviews',
        'created_at'
    )
    list_filter = ('facility_type', 'is_verified', 'is_active', 'city', 'state', 'created_at')
    search_fields = ('name', 'address', 'description', 'services')
    readonly_fields = ('average_rating', 'total_reviews', 'created_at', 'updated_at')
    inlines = [FacilityImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'facility_type', 'description', 'services')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'location')
        }),
        ('Contact', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Operating Hours', {
            'fields': (
                'monday_hours', 'tuesday_hours', 'wednesday_hours',
                'thursday_hours', 'friday_hours', 'saturday_hours', 'sunday_hours'
            ),
            'classes': ('collapse',)
        }),
        ('Amenities', {
            'fields': ('has_parking', 'has_wheelchair_access', 'has_emergency_service')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'average_rating', 'total_reviews')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Map widget settings
    map_width = 800
    map_height = 500


@admin.register(FacilityImage)
class FacilityImageAdmin(admin.ModelAdmin):
    """
    Admin for facility images
    """
    list_display = ('facility', 'caption', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('facility__name', 'caption')