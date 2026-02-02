package com.vkm.reportahealth.ui.splashscreen

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.view.View
import com.vkm.reportahealth.databinding.ActivitySplashBinding
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.home.HomeActivity
import com.vkm.reportahealth.ui.login.LoginActivity
import com.vkm.reportahealth.utils.Logger
import org.koin.android.ext.android.inject

class SplashActivity : BaseActivity() {

    private lateinit var binding: ActivitySplashBinding

    private val viewModel: AuthViewModel by inject()
    private val auth: Auth by inject()
    private val pref: SharedPreferences by inject()

    private val logger = Logger.with("splash")

    private var hasNavigated = false


    override fun onResume() {
        super.onResume()
        Log.e("LIFE", "SplashActivity onResume")
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.e("LIFE", "SplashActivity onDestroy")
    }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("SplashActivity", "SplashActivity started")

        binding = ActivitySplashBinding.inflate(layoutInflater)
        setContentView(binding.root)

        decideNextScreen()
        Log.e("LIFE", "SplashActivity onCreate")

    }

    private fun decideNextScreen() {
        Log.d("SplashActivity", "auth.accessToken=${auth.accessToken}")

        if (auth.accessToken.isNotEmpty()) {
            navigateToHome()
        } else {
            registerDeviceAndProceed()
        }
    }

    private fun registerDeviceAndProceed() {
        val deviceId = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ANDROID_ID
        )

        viewModel.registerDevice(deviceId)

        viewModel.responseLiveData().observe(this) { resource ->
            Log.d("SplashActivity", "Device registration state: ${resource.state}, data: ${resource.data}, message: ${resource.message}") // <- Add this line
            if (hasNavigated) return@observe

            when (resource.state) {

                Resource.STATE_LOADING -> {
                    binding.progressWheelSplash.visibility = View.VISIBLE
                }

                Resource.STATE_SUCCESS -> {
                    binding.progressWheelSplash.visibility = View.GONE
                    resource.data?.let {
                        if (it.isSuccess()) {
                            it.persist(pref)
                            it.persist(pref)
                            Log.d("SplashActivity", "Token after persisting: ${pref.getString("accessToken", "")}") // <- Add this line

                        }
                        navigateToLogin()
                    }
                }

                Resource.STATE_ERROR -> {
                    binding.progressWheelSplash.visibility = View.GONE
                    resource.message?.let { toast(it) }
                    navigateToLogin()
                }
            }
        }
    }

    private fun navigateToLogin() {
        if (hasNavigated) return
        hasNavigated = true

        startActivity(Intent(this, LoginActivity::class.java))
        finish()
    }

    private fun navigateToHome() {
        if (hasNavigated) return
        hasNavigated = true

        startActivity(
            Intent(this, HomeActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            }
        )
        finish()
    }
}
