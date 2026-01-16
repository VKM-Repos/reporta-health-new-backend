package com.vkm.reportahealth.utils

import android.content.SharedPreferences
import com.google.gson.Gson
import com.vkm.reportahealth.data.models.ReviewUser

object Cache {

    const val REVIEW_USER_CACHE_KEY = "review_user_"
    fun cacheReviewUser(pref: SharedPreferences, user: ReviewUser) {
        val data = Gson().toJson(user)
        pref.edit().putString(REVIEW_USER_CACHE_KEY, data).apply()
    }

    fun fetchCachedUser(pref: SharedPreferences): ReviewUser? {
        val data = pref.getString(REVIEW_USER_CACHE_KEY, "")
        if (data == "") return null

        return Gson().fromJson(data, ReviewUser::class.java) ?: null
    }
}