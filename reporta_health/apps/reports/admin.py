from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import FacilityReport, ReportImage

STATUS_COLORS = {
    "pending": "warning",
    "investigating": "info",
    "resolved": "success",
    "rejected": "danger",
}


class ReportImageInline(TabularInline):
    model = ReportImage
    extra = 0
    fields = ("image", "caption", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(FacilityReport)
class FacilityReportAdmin(ModelAdmin):
    list_display = (
        "id",
        "facility_display",
        "reason",
        "status_badge",
        "is_anonymous",
        "created_at",
    )
    list_filter = ("status", "reason", "is_anonymous", "created_at")
    search_fields = (
        "facility__name",
        "facility_name",
        "reporter__email",
        "city",
        "state",
    )
    autocomplete_fields = ("facility",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ReportImageInline]

    fieldsets = (
        (_("Facility Reference"), {
            "fields": ("facility", ("facility_name", "address"), ("city", "state"), "phone_number"),
            "description": _(
                "Either \"facility\" is set (existing facility) or the free-text fields "
                "above are (report on a facility not yet in the database)."
            ),
        }),
        (_("Report Details"), {
            "fields": ("reason", "reasons", "description"),
        }),
        (_("Reporter"), {
            "fields": ("reporter", "is_anonymous"),
        }),
        (_("Moderation"), {
            "fields": ("status", "admin_notes", "resolved_at"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    actions = ["mark_investigating", "mark_resolved", "mark_rejected"]

    @display(description=_("Facility"))
    def facility_display(self, obj):
        if obj.facility_id:
            return obj.facility.name
        return format_html(
            '<span style="opacity:0.7">(ghost) {}</span>',
            obj.facility_name or "—"
        )

    @display(description=_("Status"), label=STATUS_COLORS)
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_anonymous:
            ro.append("reporter")
        return ro

    def mark_investigating(self, request, queryset):
        queryset.update(status="investigating")
    mark_investigating.short_description = _("Mark selected reports as under investigation")

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status="resolved", resolved_at=timezone.now())
    mark_resolved.short_description = _("Mark selected reports as resolved")

    def mark_rejected(self, request, queryset):
        queryset.update(status="rejected")
    mark_rejected.short_description = _("Mark selected reports as rejected")
