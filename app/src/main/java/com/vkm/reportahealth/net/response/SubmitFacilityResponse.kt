package com.vkm.reportahealth.net.response

import com.google.gson.annotations.SerializedName

data class SubmitFacilityResponse(val message: String = "", val status: String = "",
                                  @SerializedName("status_code") val statusCode: Int = 0) {
    fun isSuccess() = statusCode >= 200 && status.uppercase() == "OK"
}