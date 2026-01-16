package com.vkm.reportahealth.utils

import android.content.SharedPreferences
import android.location.Location
import com.google.gson.Gson

class LocationHelper(private val pref: SharedPreferences) {

    val TAG = "LocalLocation"
    fun persistCurrentLocation(location: Location) {
        val local = LocalLocation(location.latitude, location.longitude)
        val json = Gson().toJson(local)

        pref.edit().putString(TAG, json).apply()
    }

    fun fetchPersistedLocation(): LocalLocation {
        val json = pref.getString(TAG, "")
        if (json == "") return LocalLocation()

        return Gson().fromJson<LocalLocation>(json, LocalLocation::class.java)
    }

    data class LocalLocation(val latitude: Double = 0.0, val longitude: Double = 0.0)
}