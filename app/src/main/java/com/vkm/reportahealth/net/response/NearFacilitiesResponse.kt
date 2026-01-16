package com.vkm.reportahealth.net.response

import com.vkm.reportahealth.data.models.Facility

class NearFacilitiesResponse(
    val data: ArrayList<Facility>,
    val status: String,
    val status_code: Int,
    val message: String
)