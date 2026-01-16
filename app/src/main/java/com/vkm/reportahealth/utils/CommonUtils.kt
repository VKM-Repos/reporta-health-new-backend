package com.vkm.reportahealth.utils

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import java.text.ParseException
import java.text.SimpleDateFormat
import java.util.regex.Pattern


/**
 * Author: Omolara Adejuwon
 * Date: 15/11/2018.
 */
open class CommonUtils {
    companion object {
        val EMAIL_ADDRESS = Pattern.compile(
            "[a-zA-Z0-9\\+\\.\\_\\%\\-\\+]{1,256}" +
                    "\\@" +
                    "[a-zA-Z0-9][a-zA-Z0-9\\-]{0,64}" +
                    "(" +
                    "\\." +
                    "[a-zA-Z0-9][a-zA-Z0-9\\-]{0,25}" +
                    ")+"
        )

        fun isEmailValid(email: String) = EMAIL_ADDRESS.matcher(email).matches()
        fun sumOfRandom(nu1: Int, nu2: Int) = nu1.plus(nu2)

        fun isPhoneNumberValid(phoneNumber: String): Boolean {
            return when {
                phoneNumber.startsWith("+234") -> phoneNumber.length == 14
                phoneNumber.startsWith("0") -> phoneNumber.length == 11
                else -> false
            }
        }

        @JvmStatic
        fun hideKeyboard(activity: Activity) {
            val view = activity.currentFocus
            if (view != null) {
                val imm = activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
                imm.hideSoftInputFromWindow(view.windowToken, 0)
            }
        }

        @JvmStatic
        fun timeInHumanFormat(time: String): String {
            //DateFormat dateInstance = SimpleDateFormat.getDateInstance();
            val formatter = SimpleDateFormat("MMMM dd, yyyy")
            val simpleDateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
            var time_format = ""
            try {
                time_format = formatter.format(simpleDateFormat.parse(time)) //Calendar.getInstance().getTime()
            } catch (e: ParseException) {
                e.printStackTrace()
            }

            return time_format
        }

    }

    @SuppressLint("all")
    fun getDeviceId(context: Context): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
    }

    fun getTimestamp(): String {
        //return SimpleDateFormat(AppConstants.TIMESTAMP_FORMAT, Locale.US).format(Date())
        return ""
    }


}