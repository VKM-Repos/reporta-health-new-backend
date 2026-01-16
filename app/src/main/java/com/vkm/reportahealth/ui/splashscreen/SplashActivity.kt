package com.vkm.reportahealth.ui.splashscreen

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.os.Handler
import android.provider.Settings
import android.view.View
import androidx.lifecycle.Observer
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.databinding.ActivityProfileBinding
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.home.HomeActivity
import com.vkm.reportahealth.utils.Logger
//import kotlinx.android.synthetic.main.activity_splash.*
import org.koin.android.ext.android.inject
import com.vkm.reportahealth.databinding.ActivitySplashBinding


class SplashActivity : BaseActivity() {
    private lateinit var binding: ActivitySplashBinding
    private val viewModel: AuthViewModel by inject()
    private val auth: Auth by inject()
    private val pref: SharedPreferences by inject()

    private val logger = Logger.with("http")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySplashBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setContentView(R.layout.activity_splash)

        // check if we still have a valid auth token
        if (auth.accessToken != "") {
            Handler().postDelayed({
                val intent = Intent(this, HomeActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                startActivity(intent)
            }, 2000)
        }else {
            val deviceId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            viewModel.registerDevice(deviceId)
            viewModel.responseLiveData().observe(this, Observer { resource ->
                when(resource.state) {
                    Resource.STATE_LOADING -> { binding.progressWheelSplash.visibility = View.VISIBLE }
                    Resource.STATE_SUCCESS -> {
                        binding.progressWheelSplash.visibility = View.GONE
                        resource.data?.let {
                            if (it.isSuccess()) {
                                it.persist(pref)
                                val intent = Intent(this, HomeActivity::class.java).apply {
                                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                }
                                startActivity(intent)
                            }else { toast(it.message) }
                        }
                    }
                    Resource.STATE_ERROR -> {
                        binding.progressWheelSplash.visibility = View.GONE
                        resource.message?.let { toast(it) }
                    } else -> {}
                }
            })
        }
    }
}
