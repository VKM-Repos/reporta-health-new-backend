package com.vkm.reportahealth.ui.base

import android.view.MenuItem
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

open class BaseActivity: AppCompatActivity() {

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        when(item?.itemId) {
            android.R.id.home -> finish()
        }
        return super.onOptionsItemSelected(item)
    }

    fun toast(message: String?) {
        message?.let { Toast.makeText(this, it, Toast.LENGTH_LONG).show() }
    }
}