package com.vkm.reportahealth.utils

import android.content.Context
import android.net.ConnectivityManager

object ConnectionUtil {

    // returns true if device is connected to the internet
    fun isConnected(context: Context): Boolean {
        val manager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val networkInfo = manager.activeNetworkInfo
        return networkInfo != null && networkInfo.isConnectedOrConnecting
    }
}