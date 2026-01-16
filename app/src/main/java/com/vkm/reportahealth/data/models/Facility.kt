package com.vkm.reportahealth.data.models

import com.google.gson.annotations.SerializedName
import org.parceler.Parcel

@Parcel
class Facility {

    val id: Int = 0

    @SerializedName("sig_unique_id")
    val sigUniqueId: String = ""

    @SerializedName("cac_reg")
    val cacReg: String = ""

    @SerializedName("comm_date")
    val commitionDate: String = ""

    @SerializedName("reg_fac_name")
    val name: String = "Facility name"

    val state: String = ""
    val statename: String = ""
    val lga: String = ""
    val lganame: String = ""
    val ward: String = ""

    @SerializedName("fac_type")
    val facilityType: Int = 0

    @SerializedName("house_no")
    val houseNo: String = ""

    @SerializedName("street_name")
    val streetName: String = ""

    val latitude: String = ""
    val longitude: String = ""

    @SerializedName("postal_address")
    val postalAddress: String = ""

    @SerializedName("phone_number")
    val phoneNumber: String = ""

    @SerializedName("email_address")
    val emailAddress: String = ""

    val website: String = ""
    val deleted: String = ""

    @SerializedName("operational_days")
    val operationDays: String = ""

    @SerializedName("hr_operation")
    val hrOperation: String = ""

    @SerializedName("hs_deleted")
    val hsDeleted: String = ""

    @SerializedName("ph_deleted")
    val phDeleted: String = ""

    @SerializedName("lab_deleted")
    val labDeleted: String = ""

    @SerializedName("im_deleted")
    val imDeleted: String = ""

    fun getLatitude(): Double {
        return try {
            latitude.toDouble()
        }catch (e: Exception) { 0.0 }
    }

    fun getLongitude(): Double {
        return try {
            longitude.toDouble()
        }catch (e: Exception) { 0.0 }
    }

    companion object {

        const val TAG = "FacilityData"
        const val STATE = "state"
    }

}