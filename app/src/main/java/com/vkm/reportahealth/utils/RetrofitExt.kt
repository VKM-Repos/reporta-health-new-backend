package com.vkm.reportahealth.utils

import okhttp3.ResponseBody
import org.json.JSONObject

/**
 * Author: Omolara Adejuwon
 * Date: 07/02/2019.
 */
fun ResponseBody.getMessage(): String {
    val json = JSONObject(this.string())
    return json.getString("message")
}