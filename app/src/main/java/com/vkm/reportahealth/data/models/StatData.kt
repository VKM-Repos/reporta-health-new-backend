package com.vkm.reportahealth.data.models

import com.google.gson.annotations.SerializedName
import org.parceler.Parcel

@Parcel
data class StatData(

        @SerializedName("LGA")
        val lga: String = "",

        @SerializedName("LGA_Id")
        val lgaId: String = "",

        @SerializedName("State")
        val state: String = "",

        @SerializedName("StateId")
        val stateId: String = "",

        @SerializedName("Pharmacy")
        val pharmacyCount: Int = 0,

        @SerializedName("Hospitals")
        val hospitalCount: Int = 0,

        @SerializedName("Laboratory")
        val labCount: Int = 0,

        @SerializedName("ImagingCenter")
        val imagingCenterCount: Int = 0)

const val StatDataKey = "StatsDataKey"
data class StatResponse(@SerializedName("status_code") val statusCode: Int = 0, val data: ArrayList<StatData>)