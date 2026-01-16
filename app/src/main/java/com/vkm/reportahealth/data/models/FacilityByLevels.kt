package com.vkm.reportahealth.data.models

/**
 * Author: Omolara Adejuwon
 * Date: 2019-06-29.
 */
data class FacilityByLevelsByOwnership(val facility_count: FacilityCount, val hospitals: List<HospitalCount>? = null)

data class FacilityByLevelsCare(val facility_count: FacilityCount, val hospitals: List<HospitalCount>? = null)

data class FacilityCount(
    val total_no_hospitals: Int = 0,
    val total_no_imaging_fac: Int = 0,
    val total_no_labs: Int = 0,
    val total_no_pharmacies: Int = 0
)

data class HospitalCount(
    val total: Int = 0,
    val ownership: Ownership? = null,
    val care_level: Care? = null
)

data class Ownership(
    val description: String
)

data class Care(val level: String)

data class FacilityByLevelsOwnershipResponse(val data: FacilityByLevelsByOwnership)
data class FacilityByLevelsCareResponse(val data: FacilityByLevelsCare)

data class ViewData(
    var facility_count: FacilityCount? = null, var hospitalsByOwnership: List<HospitalCount>? = null,
    var hospitalsByCare: List<HospitalCount>? = null
)