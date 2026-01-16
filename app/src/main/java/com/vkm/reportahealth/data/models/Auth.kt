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

    fun isSuccess() = statusText.uppercase().equals("OK") && loggedIn

    fun persist(pref: SharedPreferences) {
        val json = Gson().toJson(this)
        pref.edit().putString(KEY, json).apply()
    }
}

data class User(val username: String = "", val id: Int = 0)

data class ReviewUser(val name: String = "", val email: String = "", val phone: String = "")
