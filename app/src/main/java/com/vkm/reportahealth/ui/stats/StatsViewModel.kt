package com.vkm.reportahealth.ui.stats

import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vkm.reportahealth.data.models.StatData
import com.vkm.reportahealth.data.models.ViewData
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import kotlinx.coroutines.launch

class StatsViewModel(private val client: HttpService): ViewModel() {
    private val responseLiveData = MutableLiveData<Resource<ArrayList<StatData>>>()
    private val facitlityByLevels = MutableLiveData<Resource<ViewData>>()

    fun fetchFacilitiesCountByState() {
        val resource = Resource<ArrayList<StatData>>()
        responseLiveData.value = resource
        viewModelScope.launch {
            client.fetchFacilitiesCountInAllStates().process { response, throwable ->
                when {
                    throwable != null -> {
                        resource.state = Resource.STATE_ERROR
                        resource.message =
                            "failed to complete request. Please retry. ${throwable.localizedMessage}"
                        responseLiveData.postValue(resource)
                    }

                    response != null -> {
                        val data = response.data.sortedBy { it.state }
                        resource.state = Resource.STATE_SUCCESS
                        resource.data = ArrayList(data.toList())
                        responseLiveData.postValue(resource)
                    }
                }
            }
        }
    }
    fun fetchFacilitiesByLga(stateId: String) {
        val resource = Resource<ArrayList<StatData>>()
        responseLiveData.value = resource
        viewModelScope.launch {
            client.fetchFacilitiesCountByLga(stateId).process { response, throwable ->
                when {
                    throwable != null -> {
                        resource.state = Resource.STATE_ERROR
                        resource.message =
                            "failed to complete request. Please retry. ${throwable.localizedMessage}"
                        responseLiveData.postValue(resource)
                    }

                    response != null -> {
                        val data = response.data.sortedBy { it.lga }
                        resource.state = Resource.STATE_SUCCESS
                        resource.data = ArrayList(data)
                        responseLiveData.postValue(resource)
                    }
                }
            }
        }
    }
    fun fetchFacilitiesByLevels(stateId: String) {
        val viewData = ViewData()

        val resource = Resource<ViewData>()
        facitlityByLevels.value = resource
        viewModelScope.launch {
        client.fetchCountByOwnership(stateId).process { response, throwable ->
            when {
                throwable != null -> {
                    resource.state = Resource.STATE_ERROR
                    resource.message = "failed to complete request. Please retry. ${throwable.localizedMessage}"
                    facitlityByLevels.postValue(resource)
                }
                response != null -> {
                    val data = response.data
                    viewData.facility_count = data.facility_count
                    viewData.hospitalsByOwnership = data.hospitals

                    //facitlityByLevels.postValue(resource)
                    viewModelScope.launch {
                    client.fetchCountByCare(stateId).process { response, throwable ->
                        when {
                            throwable != null -> {
                                resource.state = Resource.STATE_ERROR
                                resource.message =
                                    "failed to complete request. Please retry. ${throwable.localizedMessage}"
                                facitlityByLevels.postValue(resource)
                            }
                            response != null -> {
                                val data = response.data
                                viewData.hospitalsByCare = response.data.hospitals
                                resource.state = Resource.STATE_SUCCESS
                                resource.data = viewData
                                facitlityByLevels.postValue(resource)
                            }
                        }
                    }
                }
            }
        }
    }}}

    fun responseLiveData() = responseLiveData
    fun facilityByLevels() = facitlityByLevels
}