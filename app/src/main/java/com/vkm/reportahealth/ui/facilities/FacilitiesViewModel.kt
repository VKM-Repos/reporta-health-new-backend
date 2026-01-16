package com.vkm.reportahealth.ui.facilities

import android.app.Application
import android.location.Location
import android.os.Looper
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.google.android.gms.location.*
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.net.Simple
import com.vkm.reportahealth.net.response.SearchFacilitiesResponse
import com.vkm.reportahealth.utils.Logger
import java.util.*


class FacilitiesViewModel(private val httpService: HttpService,
                          private val app: Application): ViewModel() {

    private val locationUpdatesLiveData = MutableLiveData<Location>()
    private val facilitiesLiveData = MutableLiveData<Resource<ArrayList<Facility>>>()
    private val searchResultLiveData = MutableLiveData<Resource<ArrayList<Facility>>>()
    private val errorLiveData = MutableLiveData<String>()
    private val logger = Logger.with("http")
    var requestCall: Simple<SearchFacilitiesResponse>? = null
    private var facilities = ArrayList<Facility>()
    private var lastKeyword = ""

    companion object {
        const val UPDATE_INTERVAL: Long = 60 * 1000 // 60 seconds
        const val FASTEST_INTERVAL: Long = 5 * 1000 // 5 seconds
    }

    fun startLocationUpdates() {
        setUpAndStartLocationUpdates()
    }

    private fun setUpAndStartLocationUpdates() {
        val request = LocationRequest().apply {
            priority = LocationRequest.PRIORITY_BALANCED_POWER_ACCURACY
            interval = UPDATE_INTERVAL
            fastestInterval = FASTEST_INTERVAL
        }

        val builder = LocationSettingsRequest.Builder()
        builder.addLocationRequest(request)
        val locationSettingsRequest = builder.build()

        val settingsClient = LocationServices.getSettingsClient(app.applicationContext)
        settingsClient.checkLocationSettings(locationSettingsRequest)

        val locationCallback = object: LocationCallback() {
            override fun onLocationResult(p0: LocationResult?) {

                val location = p0?.lastLocation
                locationUpdatesLiveData.value = location

                stopLocationUpdates(this)
            }
        }

        requestLocationUpdates(request, locationCallback)
    }

    private fun requestLocationUpdates(request: LocationRequest, cb: LocationCallback) {
        try {
            LocationServices.getFusedLocationProviderClient(app.applicationContext).requestLocationUpdates(request, cb, Looper.myLooper())
        }catch (e: SecurityException) {}
    }

    private fun stopLocationUpdates(cb: LocationCallback) {
        LocationServices.getFusedLocationProviderClient(app.applicationContext).removeLocationUpdates(cb)
    }


    fun loadFacilities(currentLocation: Location, facType: Int ) {

        val resource = Resource<ArrayList<Facility>>()
        facilitiesLiveData.postValue(resource)

        httpService.fetchNearestFacilities(
            currentLocation.latitude,
            currentLocation.longitude, facType
        ).process { response, throwable ->
                    when {
                        response != null -> {
                            if (response.status_code in 400..505) {
                                errorLiveData.postValue(response.message)
                            } else {
                                if (response.data.isNotEmpty()) {
                                    facilities.clear()
                                }
                                facilities.addAll(response.data)
                                resource.state = Resource.STATE_SUCCESS
                                resource.data = facilities
                                facilitiesLiveData.postValue(resource)
                            }
                        }
                        throwable != null -> {
                            logger.log("Error $throwable")

                            errorLiveData.postValue(throwable.message)
                        }
                    }
                }
    }


    fun searchFacilities(keyWord: String) {
        if (keyWord.length < 3) return //this is done so as to ensure reasonable search query and inturn improve performance
        val resource = Resource<ArrayList<Facility>>().apply { state = Resource.STATE_LOADING }
        searchResultLiveData.value = resource
        requestCall?.cancel()
        requestCall = httpService.search(keyWord)
        requestCall!!.process { response, throwable ->
            when {
                response != null -> {
                    val data = response.data
                    if (data != null) {
                        resource.state = Resource.STATE_SUCCESS
                        resource.data = data.facilities
                        searchResultLiveData.postValue(resource)

                        logger.log("Search result data => ${data.facilities.size}")
                    }
                }
                throwable != null -> {
                    errorLiveData.postValue(throwable.message)
                }
            }
        }
    }

    fun getFacilities() = facilities

    fun searchResultLiveData() = searchResultLiveData

    fun locationUpdatesListener() = locationUpdatesLiveData

    fun facilitiesLiveData() = facilitiesLiveData

    fun errorLiveData() = errorLiveData

}