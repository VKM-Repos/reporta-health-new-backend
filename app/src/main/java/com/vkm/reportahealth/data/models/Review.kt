package com.vkm.reportahealth.data.models

import com.google.gson.annotations.SerializedName

class Review(@SerializedName("name") val username: String = "",
            @SerializedName("created_at") val reportTime: String = "",
             @SerializedName("content") val reportText: String = "")