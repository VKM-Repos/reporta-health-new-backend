package com.vkm.reportahealth.ui.facilities

import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.data.models.Review
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.net.payloads.ReviewFacilityPayload
import com.vkm.reportahealth.net.response.ReviewFacilityResponse

class FacilityReviewViewModel(private val service: HttpService,
                              private val auth: Auth): ViewModel() {

    private val reviewsLiveData = MutableLiveData<Resource<ArrayList<Review>>>()
    private val submitReviewLiveData = MutableLiveData<Resource<ReviewFacilityResponse>>()

    suspend fun fetchReviews(id: String) {

        val resource = Resource<ArrayList<Review>>()
        reviewsLiveData.value = resource

        service.fetchReviews(id).process { response, throwable ->
            when {
                response != null -> {
                    val data = response.data
                    resource.state = Resource.STATE_SUCCESS
                    resource.data = data
                    reviewsLiveData.postValue(resource)
                }
                throwable != null -> {
                    resource.state = Resource.STATE_ERROR
                    resource.message = "failed to complete request. Please retry. ${throwable.localizedMessage}"
                    reviewsLiveData.postValue(resource)
                }
            }
        }
    }

    suspend fun submitReview(facilityId: String, content: String) {
        val resource = Resource<ReviewFacilityResponse>()
        submitReviewLiveData.value = resource

        var userId: Int = 0
        if (auth.user?.id != null) userId = auth.user.id

        service.postReview(ReviewFacilityPayload(userId,
                facilityId, content)).process { response, throwable ->
            when {
                response != null -> {
                    resource.state = Resource.STATE_SUCCESS
                    resource.data = response
                    submitReviewLiveData.postValue(resource)
                }
                throwable != null -> {
                    resource.state = Resource.STATE_ERROR
                    resource.message = "failed to post review at the moment. Please retry. ${throwable.localizedMessage}"
                    submitReviewLiveData.postValue(resource)
                }
            }
        }
    }

    fun reviewLiveData() = reviewsLiveData

    fun submitReviewLiveData() = submitReviewLiveData
}