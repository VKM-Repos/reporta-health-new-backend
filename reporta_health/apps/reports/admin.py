"""
Admin configuration for Report models
"""

from django.contrib import admin
from django.utils import timezone
from .models import FacilityReport, ReportImage


class ReportImageInline(admin.TabularInline):
    """
    Inline admin for report images
    """
    model = ReportImage
    extra = 0
    fields = ('image', 'caption', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(FacilityReport)
class FacilityReportAdmin(admin.ModelAdmin):
    """
    Admin for facility reports
    """
    list_display = (
        'id',
        'facility',
        'reporter',
        'reason',
        'status',
        'created_at',
        'resolved_at'
    )
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('facility__name', 'reporter__email', 'description')
    readonly_fields = ('reporter', 'created_at', 'updated_at')
    inlines = [ReportImageInline]
    
    fieldsets = (
        ('Report Information', {
            'fields': ('facility', 'reporter', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes', 'resolved_at')
        }),
        ('Images', {
            'fields': (),
            'description': 'Evidence images are shown below'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_rejected']
    
    def mark_as_investigating(self, request, queryset):
        """Mark selected reports as under investigation"""
        updated = queryset.update(status='investigating')
        self.message_user(request, f'{updated} report(s) marked as under investigation.')
    mark_as_investigating.short_description = "Mark as investigating"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved"""
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} report(s) marked as resolved.')
    mark_as_resolved.short_description = "Mark as resolved"
    
    def mark_as_rejected(self, request, queryset):
        """Mark selected reports as rejected"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} report(s) marked as rejected.')
    mark_as_rejected.short_description = "Mark as rejected"


@admin.register(ReportImage)
class ReportImageAdmin(admin.ModelAdmin):
    """
    Admin for report images
    """
    list_display = ('report', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('report__facility__name', 'caption')
    readonly_fields = ('uploaded_at',)