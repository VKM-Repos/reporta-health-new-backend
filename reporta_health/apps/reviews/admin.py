"""
Admin configuration for Review models
"""

from django.contrib import admin
from .models import Review, ReviewImage


class ReviewImageInline(admin.TabularInline):
    """
    Inline admin for review images
    """
    model = ReviewImage
    extra = 0
    fields = ('image', 'caption', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin for reviews
    """
    list_display = (
        'facility',
        'user',
        'rating',
        'body',
        'is_verified',
        'helpful_count',
        'created_at'
    )
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('facility__name', 'user__email', 'body')
    readonly_fields = ('user', 'facility', 'helpful_count', 'created_at', 'updated_at')
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('facility', 'user', 'rating', 'body', 'visit_date')
        }),
        ('Status', {
            'fields': ('is_verified', 'helpful_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_reviews', 'unverify_reviews']
    
    def verify_reviews(self, request, queryset):
        """Mark selected reviews as verified"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} review(s) marked as verified.')
    verify_reviews.short_description = "Mark as verified"
    
    def unverify_reviews(self, request, queryset):
        """Mark selected reviews as unverified"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} review(s) marked as unverified.')
    unverify_reviews.short_description = "Mark as unverified"


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    """
    Admin for review images
    """
    list_display = ('review', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('review__facility__name', 'caption')
    readonly_fields = ('uploaded_at',)