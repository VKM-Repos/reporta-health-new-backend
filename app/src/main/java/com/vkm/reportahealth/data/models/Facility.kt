package com.vkm.reportahealth.data.models

import com.google.gson.annotations.SerializedName
import org.parceler.Parcel
import org.parceler.ParcelConstructor

@Parcel(Parcel.Serialization.BEAN)
class Facility(

    var lganame: String = "",
    var statename: String = "",

    @SerializedName("fac_type")
    var facilityType: Int = 0

) {
    @SerializedName("id")
    var id: Int = 0

    @SerializedName("sig_unique_id")
    var sigUniqueId: String = ""

    @SerializedName("cac_reg")
    var cacReg: String = ""

    @SerializedName("reg_fac_name")
    var name: String = "Facility name"

    var state: String = ""
    var lga: String = ""
    var ward: String = ""

    @SerializedName("house_no")
    var houseNo: String = ""

    @SerializedName("street_name")
    var streetName: String = ""

    var latitude: String = ""
    var longitude: String = ""

    @SerializedName("postal_address")
    var postalAddress: String = ""

    @SerializedName("phone_number")
    var phoneNumber: String = ""

    @SerializedName("email_address")
    var emailAddress: String = ""

    var website: String = ""

    @SerializedName("operational_days")
    var operationDays: String = ""

    @SerializedName("hr_operation")
    var hrOperation: String = ""

    // Rename these so they don't clash with the 'latitude' and 'longitude' variables
    fun fetchLatitude(): Double = try { latitude.toDouble() } catch (e: Exception) { 0.0 }
    fun fetchLongitude(): Double = try { longitude.toDouble() } catch (e: Exception) { 0.0 }

    companion object {
        const val TAG = "FacilityData"
        const val STATE = "state"
    }
}
