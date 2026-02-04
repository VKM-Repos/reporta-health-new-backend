package com.vkm.reportahealth.data.models

import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName

class Auth {

    companion object {
        const val KEY = "AuthSaveKey"

        fun currentAuth(pref: SharedPreferences): Auth {
            val json = pref.getString(KEY, "")
            return if (json == "") Auth() else Gson().fromJson(json, Auth::class.java)
        }
    }

    val accessToken: String = ""

    @SerializedName("loggedin")
    val loggedIn: Boolean = false

    val statusText: String = ""

    val message: String = ""

    @SerializedName("user")
    val user: User? = null

    fun login(email: String, password: String, callback: (Boolean, String) -> Unit) {
        // 1. Validation
        if (email.isBlank() || password.isBlank()) {
            callback(false, "Email and password are required")
            return
        }

        // 2. Here is where you will place your network logic
        // For now, this is the 'Simple' boilerplate for a network call:




        // TEST MOCK: Delete this once your API is ready
        if (email == "test@test.com" && password == "1234") {
            callback(true, "Success")
        } else {
            callback(false, "Invalid credentials")
        }
    }
    fun isSuccess() = statusText.uppercase().equals("OK") && loggedIn

    fun persist(pref: SharedPreferences) {
        val json = Gson().toJson(this)
        pref.edit().putString(KEY, json).apply()
    }
}

data class User(val username: String = "", val id: Int = 0)

data class ReviewUser(val name: String = "", val email: String = "", val phone: String = "")
