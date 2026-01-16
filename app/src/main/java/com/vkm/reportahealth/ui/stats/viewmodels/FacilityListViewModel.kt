package com.vkm.reportahealth.ui.stats.viewmodels

import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import java.util.*

/**
 * Author: Omolara Adejuwon
 * Date: 2019-08-20.
 */
class FacilityListViewModel(private val httpService: HttpService) : ViewModel() {

    private val facilitiesLiveData = MutableLiveData<Resource<ArrayList<Facility>>>()
    private val errorLiveData = MutableLiveData<String>()
    private var facilities = ArrayList<Facility>()

    fun loadFacilities(lgaId: String?, state: String?, page: Int = 0, count: Int = 10) {

        val resource = Resource<ArrayList<Facility>>()
        facilitiesLiveData.postValue(resource)

        httpService.fetchFacilitiesByLga(
            lgaId, state, page, count
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
                    throwable.printStackTrace()

                    errorLiveData.postValue(throwable.message)
                }
            }
        }
    }
fun responseLiveData() = facilitiesLiveData
    fun errorLiveData() = errorLiveData
}