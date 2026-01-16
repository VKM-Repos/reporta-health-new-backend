package com.vkm.reportahealth.data.models

import org.parceler.Parcel

@Parcel
class FacilityType(var icon: Int = 0, var title: String? = "", var id: Int = 0) {

    companion object {
        const val TAG = "FacilityTypeTag"
    }
}