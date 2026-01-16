package com.vkm.reportahealth.net.response

import com.google.gson.annotations.SerializedName
import com.vkm.reportahealth.data.models.Review

data class ReviewFacilityResponse(val status: String = "", @SerializedName("status_code") val statusCode: Int = 0,
                                  val data: String = "")

data class FetchFacilitiesResponse(val page: Int = 0,
                                   val data: ArrayList<Review>)

