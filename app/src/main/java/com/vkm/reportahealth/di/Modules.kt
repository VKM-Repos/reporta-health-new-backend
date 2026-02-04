package com.vkm.reportahealth.di

import android.preference.PreferenceManager
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.SimpleAdapterFactory
import com.vkm.reportahealth.ui.facilities.*
import com.vkm.reportahealth.ui.splashscreen.AuthViewModel
import com.vkm.reportahealth.ui.stats.StatsViewModel
import com.vkm.reportahealth.ui.stats.viewmodels.FacilityListViewModel
import com.vkm.reportahealth.utils.LocationHelper
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import org.koin.android.ext.koin.androidApplication
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.core.qualifier.named
import org.koin.dsl.module
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

// ===================== CONSTANTS =====================

const val BASE_URL = "https://api.reportahealth.org/v1/"

const val AUTH_INTERCEPTOR = "auth_interceptor"
const val LOGGING_INTERCEPTOR_KEY = "logging_interceptor"
const val ACCEPT_HEADER_INJECTOR = "accept_header_injector"

const val AUTHENTICATED_HTTP_SERVICE = "authenticated_http_service"
const val UNAUTHENTICATED_HTTP_SERVICE = "unauthenticated_http_service"

// ===================== OKHTTP HELPER =====================

private fun baseClient(): OkHttpClient.Builder =
    OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)

// ===================== APP MODULE =====================

val appModule = module {

    single { PreferenceManager.getDefaultSharedPreferences(androidApplication()) }
    single { LocationHelper(get()) }

    // Auth holder (reads token from prefs internally)
    single { Auth.currentAuth(get()) }

    // ViewModels
    viewModel { AuthViewModel(get(named(UNAUTHENTICATED_HTTP_SERVICE)), get()) }

    viewModel {
        FacilitiesViewModel(
            get(named(AUTHENTICATED_HTTP_SERVICE)),
            androidApplication()
        )
    }

    viewModel {
        FacilityReviewViewModel(
            get(named(AUTHENTICATED_HTTP_SERVICE)),
            get()
        )
    }

    viewModel {
        SubmitFacilityViewModel(
            get(named(AUTHENTICATED_HTTP_SERVICE)),
            androidApplication(),
            get(),
            get()
        )
    }

    viewModel { StatsViewModel(get(named(AUTHENTICATED_HTTP_SERVICE))) }
    viewModel { FacilityListViewModel(get(named(AUTHENTICATED_HTTP_SERVICE))) }
}

// ===================== NETWORK MODULE =====================

val networkModule = module {

    // ---------- Logging ----------
    single(named(LOGGING_INTERCEPTOR_KEY)) {
        HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
    }

    // ---------- Accept Header ----------
    single(named(ACCEPT_HEADER_INJECTOR)) {
        Interceptor { chain ->
            val request = chain.request()
                .newBuilder()
                .addHeader("Accept", "application/json")
                .build()
            chain.proceed(request)
        }
    }

    // ---------- Auth Header (SAFE) ----------
    single(named(AUTH_INTERCEPTOR)) {
        Interceptor { chain ->
            val auth: Auth = get()
            val request = chain.request()
                .newBuilder()
                .addHeader("Authorization", "Bearer ${auth.accessToken}")
                .build()
            chain.proceed(request)
        }
    }

    // ---------- UNAUTHENTICATED SERVICE ----------
    single(named(UNAUTHENTICATED_HTTP_SERVICE)) {

        val client = baseClient()
            .addInterceptor(get<Interceptor>(named(ACCEPT_HEADER_INJECTOR)))
            .addInterceptor(get<HttpLoggingInterceptor>(named(LOGGING_INTERCEPTOR_KEY)))
            .build()

        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .addCallAdapterFactory(SimpleAdapterFactory.create())
            .build()
            .create(HttpService::class.java)
    }

    // ---------- AUTHENTICATED SERVICE ----------
    single(named(AUTHENTICATED_HTTP_SERVICE)) {

        val client = baseClient()
            .addInterceptor(get<Interceptor>(named(ACCEPT_HEADER_INJECTOR)))
            .addInterceptor(get<Interceptor>(named(AUTH_INTERCEPTOR)))
            .addInterceptor(get<HttpLoggingInterceptor>(named(LOGGING_INTERCEPTOR_KEY)))
            .build()

        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .addCallAdapterFactory(SimpleAdapterFactory.create())
            .build()
            .create(HttpService::class.java)
    }
}

// ===================== MODULE LIST =====================

val appModules = listOf(
    appModule,
    networkModule
)




