package com.vkm.reportahealth.net

import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.data.models.FacilityByLevelsCareResponse
import com.vkm.reportahealth.data.models.FacilityByLevelsOwnershipResponse
import com.vkm.reportahealth.data.models.StatResponse
import com.vkm.reportahealth.net.payloads.DeviceData
import com.vkm.reportahealth.net.payloads.ReportFacilityPayload
import com.vkm.reportahealth.net.payloads.ReviewFacilityPayload
import com.vkm.reportahealth.net.response.*
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query


interface HttpService {

    @POST("register")
    suspend fun registerDevice(
        @Body device: DeviceData
    ): Simple<Auth>

    @GET("fetch_nearest_facilities")
    suspend fun fetchNearestFacilities(
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
        @Query("fac_type") facType: Int?
    ): Simple<NearFacilitiesResponse>

    @POST("report")
    suspend fun reportFacility(
        @Body data: ReportFacilityPayload
    ): Simple<SubmitFacilityResponse>

    @GET("search")
    suspend fun search(
        @Query("query") query: String
    ): Simple<SearchFacilitiesResponse>

    @POST("review")
    suspend fun postReview(
        @Body review: ReviewFacilityPayload
    ): Simple<ReviewFacilityResponse>

    @GET("review")
    suspend fun fetchReviews(
        @Query("facility_id") facilityId: String
    ): Simple<FetchFacilitiesResponse>

    @GET("facility_count_in_all_states")
    suspend fun fetchFacilitiesCountInAllStates(): Simple<StatResponse>

    @GET("facility_count_in_state_by_lgas")
    suspend fun fetchFacilitiesCountByLga(
        @Query("state") stateId: String?
    ): Simple<StatResponse>

    @GET("facility_count_by_state_ownership")
    suspend fun fetchCountByOwnership(
        @Query("state") stateId: String?
    ): Simple<FacilityByLevelsOwnershipResponse>

    @GET("facility_count_by_state_care_level")
    suspend fun fetchCountByCare(
        @Query("state") stateId: String?
    ): Simple<FacilityByLevelsCareResponse>

    @GET("fetch_facilities_by_lga_details")
    suspend fun fetchFacilitiesByLga(
        @Query("lga") lgaId: String?,
        @Query("state") state: String?,
        @Query("page") page: Int = 1,
        @Query("count") count: Int = 10
    ): Simple<NearFacilitiesResponse>
}



