"""
Serializers for SARC endpoints
"""

from rest_framework import serializers
from .models import SARCProfile, Facility
from .serializers import FacilityListSerializer


class SARCProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SARCProfile
        fields = (
            'unit_name',
            'hotline_number',
            'is_24_hours',
            'accepts_walk_ins',
            'confidentiality_assured',
            'has_police_presence',
            'has_legal_aid',
            'has_counseling',
            'has_hiv_pep',
            'has_emergency_contraception',
            'has_shelter_referral',
            'has_forensic',
            'has_sti_testing',
            'has_court_support',
            'languages',
            'additional_info',
        )


class SARCFacilitySerializer(FacilityListSerializer):
    """
    Facility serializer with nested SARC profile.
    Extends the list serializer so distance works for nearby queries.
    """
    sarc_profile = SARCProfileSerializer(read_only=True)
    is_standalone_sarc = serializers.SerializerMethodField()

    class Meta(FacilityListSerializer.Meta):
        fields = FacilityListSerializer.Meta.fields + (
            'has_sarcs',
            'sarc_profile',
            'is_standalone_sarc',
        )

    def get_is_standalone_sarc(self, obj):
        return obj.facility_type == 'sarcs'