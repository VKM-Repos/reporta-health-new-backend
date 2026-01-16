package com.vkm.reportahealth.ui.facilities

import android.app.Application
import android.location.Address
import android.location.Geocoder
import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.net.payloads.ReportFacilityPayload
import com.vkm.reportahealth.net.response.SubmitFacilityResponse
import com.vkm.reportahealth.utils.LocationHelper
import java.util.*
import java.util.concurrent.Executors

class SubmitFacilityViewModel(private val httpService: HttpService, private val app: Application,
                              private val auth: Auth,
                              val location: LocationHelper): ViewModel() {

    val EMPTY_RESPONSE = ""

    private val progressLiveData = MutableLiveData<Resource<SubmitFacilityResponse>>()
    private val addressLiveData = MutableLiveData<String>()
    private val executor = Executors.newSingleThreadExecutor()

    fun submitFacility(
        facilityName: String, facilityCategory: Int, location: String,
        name: String, email: String, phone: String) {

        var userId = 0
        if (auth.user?.id != null) {
            userId = auth.user.id
        }

        val payload = ReportFacilityPayload(userId,
            facilityName,
            facilityCategory = facilityCategory,
            name = name,
            email = email,
            phone = phone,
            location = location
        )
        Log.e("payload", payload.toString())
        val resource = Resource<SubmitFacilityResponse>()
        progressLiveData.value = resource

        httpService.reportFacility(payload).process { response, throwable ->
            when {
                response != null -> {
                    resource.state = Resource.STATE_SUCCESS
                    resource.data = response
                    progressLiveData.postValue(resource)
                }
                throwable != null -> {
                    resource.state = Resource.STATE_ERROR
                    resource.message = response?.message ?: "failed to submit facility. ${throwable.localizedMessage}"
                    progressLiveData.postValue(resource)
                }
            }
        }
    }

    fun fetchCurrentLocationAddress(locb: LocationHelper.LocalLocation? = null) {
        executor.execute {
            var addresses: List<Address> = emptyList()
            try {
                val geoCoder = Geocoder(app.applicationContext, Locale.getDefault())
                val loc = locb ?: location.fetchPersistedLocation()
                addresses = geoCoder.getFromLocation(loc.latitude, loc.longitude, 1)!!
                if (addresses.isNotEmpty()) {
                    val address = addresses[0]
                    val addressString = with(address) {
                        (0..maxAddressLineIndex).map { getAddressLine(it) }
                    }

                    addressLiveData.postValue(addressString.joinToString("\n"))
                }else {
                    addressLiveData.postValue(EMPTY_RESPONSE)
                }
            }catch (e: Exception) { addressLiveData.postValue(EMPTY_RESPONSE) }
        }
    }

    fun liveData() = progressLiveData

    fun locationAddressLiveData() = addressLiveData
}