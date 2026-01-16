package com.vkm.reportahealth.net.response

import com.google.gson.annotations.SerializedName
import com.vkm.reportahealth.data.models.Facility

class SearchFacilitiesResponse {
    val data: Data? = null
}

data class Data(@SerializedName("current_page") val currentPage: Int = 0,
                @SerializedName("data") val facilities: ArrayList<Facility>)