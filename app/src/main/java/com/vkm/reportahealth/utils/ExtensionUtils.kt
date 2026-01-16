package com.vkm.reportahealth.utils

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Build
import android.text.*
import android.widget.EditText
import android.widget.TextView
import androidx.core.app.ActivityCompat
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LiveData
import androidx.lifecycle.Observer
import java.net.ConnectException
import java.net.SocketException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

/**
 * Author: Omolara Adejuwon
 * Date: 06/12/2018.
 */
fun String.toEditable(): Editable = Editable.Factory.getInstance().newEditable(this)

fun String.isValidEmail(): Boolean = CommonUtils.isEmailValid(this)
fun String.isValidPhoneNumber(): Boolean = CommonUtils.isPhoneNumberValid(this)
fun String.isValidPassword(): Boolean = !TextUtils.isEmpty(this)
fun String.isValidText(): Boolean = !TextUtils.isEmpty(this)

fun Context.isGPSEnabled() = (getSystemService(Context.LOCATION_SERVICE) as LocationManager).isProviderEnabled(
    LocationManager.GPS_PROVIDER
)

fun Context.checkLocationPermission() =
    ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED

fun Activity.hideKeyboard() = CommonUtils.hideKeyboard(this)

fun EditText.onTextChange(f: (String) -> Unit) {
    this.addTextChangedListener(object: TextWatcher {
        override fun afterTextChanged(s: Editable?) {}

        override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}

        override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
            val newValue = s?.toString() ?: ""
            f(newValue)
        }
    })
}

fun TextView.onTextChanged(f: (String) -> Unit) {
    this.addTextChangedListener(object: TextWatcher {
        override fun afterTextChanged(s: Editable?) {}
        override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
        override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
            val newValue = s?.toString() ?: ""
            f(newValue)
        }
    })
}

fun <T : Any, L : LiveData<T>> LifecycleOwner.observe(liveData: L, body: (T?) -> Unit) {
    liveData.observe(this, Observer(body))
}

fun Throwable.multiCatch(block: () -> Unit, block2: () -> Unit) {
    when (this) {
        is SocketTimeoutException, is UnknownHostException, is SocketException, is ConnectException -> {
            block()
        }
        else -> {
            block2()
        }
    }
}
val String.loadHtml: Spanned
    get() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            return  Html.fromHtml(this, Html.FROM_HTML_MODE_LEGACY)
        } else {
            @Suppress("DEPRECATION")
            return Html.fromHtml(this)
        }
    }
fun String.capitalizeWords(): String = split(" ").map { it.capitalize() }.joinToString(" ")


