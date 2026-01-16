package com.vkm.reportahealth.net.payloads

import com.google.gson.annotations.SerializedName

data class DeviceData(@SerializedName("username") val deviceId: String = "", val password: String = "")

data class ReportFacilityPayload(@SerializedName("user_id") val userId: Int = 0,
                                 @SerializedName("facility_name") val facilityName: String = "",
                                 @SerializedName("facility_categoryd") val facilityCategoryD: String="",
                                 @SerializedName("facility_category") val facilityCategory: Int=0,
                                 val name: String = "",
                                 val email: String = "",
                                 val phone: String = "",
                                 val location: String = "",
                                 val complaints_factor: List<Int> = emptyList(),
                                 val other_complaints_factor: String = "",
                                 val facility_on_reporta_health: Int = 0,
                                 val can_navigate: String = "",
                                 val gps_point_lat: String = "",
                                 val gps_point_lon: Double = 0.0,
                                 val state: String = "")

data class ReviewFacilityPayload(@SerializedName("user_id") val userId: Int = 0,
                                 @SerializedName("facility_id") val facilityId: String = "",
                                 val content: String = "")