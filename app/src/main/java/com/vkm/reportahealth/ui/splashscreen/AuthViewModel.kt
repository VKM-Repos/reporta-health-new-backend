package com.vkm.reportahealth.ui.splashscreen

import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.net.payloads.DeviceData
import java.util.*

class AuthViewModel(private val httpService: HttpService, private val auth: Auth): ViewModel() {

    private val responseLiveData = MutableLiveData<Resource<Auth>>()
    fun registerDevice(deviceId: String = "") {

        val resource = Resource<Auth>()
        // generate a random UUID
        // incase deviceId is absent
        val deviceID = if (deviceId == "") UUID.randomUUID().toString() else deviceId

        // notify attached conponent
        // that network request has started
        resource.state = Resource.STATE_LOADING
        responseLiveData.value = resource

        val password = "android$deviceID"
        val data = DeviceData(deviceId, password)
        httpService.registerDevice(data).process { auth, throwable ->
            when {
                auth != null -> {
                    resource.state = Resource.STATE_SUCCESS
                    resource.data = auth
                    responseLiveData.postValue(resource)
                }
                throwable != null -> {
                    val message = throwable.message ?: "failed to complete request. Please retry"
                    resource.state = Resource.STATE_ERROR
                    resource.message = message
                    responseLiveData.postValue(resource)
                }
            }
        }
    }

    fun responseLiveData() = responseLiveData
}