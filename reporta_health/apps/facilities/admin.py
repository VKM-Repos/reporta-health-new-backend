from django import forms
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.geos import Point
from unfold.admin import ModelAdmin
from .models import Facility


class FacilityAdminForm(forms.ModelForm):
    latitude = forms.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        help_text="Precise latitude, e.g. 6.524379"
    )
    longitude = forms.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        help_text="Precise longitude, e.g. 3.379206"
    )

    class Meta:
        model = Facility
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance and instance.pk and instance.location:
            self.fields["latitude"].initial = instance.location.y
            self.fields["longitude"].initial = instance.location.x

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")
        if lat is not None and lon is not None:
            cleaned_data["location"] = Point(float(lon), float(lat), srid=4326)
        return cleaned_data


@admin.register(Facility)
class FacilityAdmin(GISModelAdmin, ModelAdmin):
    form = FacilityAdminForm
    list_display = ["name", "facility_type", "has_gbv_services", "has_sarcs", "has_fistula_programme", "created_at"]
    list_filter = ["facility_type", "has_gbv_services", "has_sarcs", "has_fistula_programme"]
    search_fields = ["name", "address", "city", "state", "lga"]
    readonly_fields = ("average_rating", "total_reviews", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "facility_type", "ownership", "care_level", "description")
        }),
        ("Contact", {
            "fields": ("phone_number", "email", "website")
        }),
        ("Location", {
            "fields": ("latitude", "longitude", "location", "address", "city", "state", "lga"),
            "description": "Enter precise latitude/longitude below, or click the map (map is approximate)."
        }),
        ("Operating Hours", {
            "fields": ("operating_hours", "monday_hours", "tuesday_hours", "wednesday_hours",
                       "thursday_hours", "friday_hours", "saturday_hours", "sunday_hours"),
            "classes": ("collapse",)
        }),
        ("Services & Amenities", {
            "fields": ("services", "has_parking", "has_wheelchair_access", "has_emergency_service")
        }),
        ("GBV / Specialized Services", {
            "fields": ("has_gbv_services", "has_sarcs", "has_fistula_programme")
        }),
        ("Status", {
            "fields": ("is_verified", "is_active", "sig_unique_id")
        }),
        ("Stats (read-only)", {
            "fields": ("average_rating", "total_reviews", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    gis_widget_kwargs = {
        "attrs": {
            "default_lon": 8.6753,
            "default_lat": 9.0820,
            "default_zoom": 6,
        }
    }
