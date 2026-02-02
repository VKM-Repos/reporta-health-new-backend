package com.vkm.reportahealth.di

import android.preference.PreferenceManager
import android.util.Log
import com.vkm.reportahealth.data.models.Auth
import com.vkm.reportahealth.net.HttpService
import com.vkm.reportahealth.net.SimpleAdapterFactory
import com.vkm.reportahealth.ui.facilities.FacilitiesViewModel
import com.vkm.reportahealth.ui.facilities.FacilityReviewViewModel
import com.vkm.reportahealth.ui.facilities.SubmitFacilityViewModel
import com.vkm.reportahealth.ui.splashscreen.AuthViewModel
import com.vkm.reportahealth.ui.stats.StatsViewModel
import com.vkm.reportahealth.ui.stats.viewmodels.FacilityListViewModel
import com.vkm.reportahealth.utils.LocationHelper
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import org.koin.android.ext.koin.androidApplication
// Replace org.koin.dsl.module.module
import org.koin.dsl.module

// Replace org.koin.android.viewmodel.ext.koin.viewModel
import org.koin.androidx.viewmodel.dsl.viewModel

//new code
import org.koin.core.qualifier.named

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

const val AUTH_INTERCEPTOR = "auth_interceptor"
const val LOGGING_INTERCEPTOR_KEY = "logging_interceptor"
const val AUTHENTICATED_RETROFIT = "authenticated_retrofit"
const val AUTHENTICATED_HTTP_SERVICE = "authenticated_http_service"
const val UNAUTHENTICATED_RETROFIT = "unauthenticated_retrofit"
const val UNAUTHENTICATED_HTTP_SERVICE = "unauthenticated_http_service"
const val ACCEPT_HEADER_INJECTOR = "accept_header_injector"
const val BASE_URL = "https://api.reportahealth.org/v1/"

val appModule = module {
    single { PreferenceManager.getDefaultSharedPreferences(androidApplication()) }
    factory { LocationHelper(get()) }
    factory { Auth.currentAuth(get()) }
    // In Modern Koin, use named() for your keys
    viewModel { FacilitiesViewModel(get(named(AUTHENTICATED_HTTP_SERVICE)), androidApplication()) }
    viewModel { AuthViewModel(get(named(UNAUTHENTICATED_HTTP_SERVICE)), get()) }
    viewModel { FacilityReviewViewModel(get(named(AUTHENTICATED_HTTP_SERVICE)), get()) }

// If LocationHelper is a simple class, get() will find it if it's defined elsewhere
    viewModel { SubmitFacilityViewModel(get(named(AUTHENTICATED_HTTP_SERVICE)), androidApplication(), get(), LocationHelper(get())) }

    viewModel { StatsViewModel(get(named(AUTHENTICATED_HTTP_SERVICE))) }
    viewModel { FacilityListViewModel(get(named(AUTHENTICATED_HTTP_SERVICE))) }
//    viewModel { FacilitiesViewModel(get(AUTHENTICATED_HTTP_SERVICE), androidApplication()) }
//    viewModel { AuthViewModel(get(UNAUTHENTICATED_HTTP_SERVICE), get()) }
//    viewModel { FacilityReviewViewModel(get(AUTHENTICATED_HTTP_SERVICE), get()) }
//    viewModel { SubmitFacilityViewModel(get(AUTHENTICATED_HTTP_SERVICE), androidApplication(), get(), LocationHelper(get())) }
//    viewModel { StatsViewModel(get(AUTHENTICATED_HTTP_SERVICE)) }
//    viewModel { FacilityListViewModel(get(AUTHENTICATED_HTTP_SERVICE)) }
}

val networkModule = module {

    factory {
        OkHttpClient.Builder()
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
    }

    single(qualifier = named(LOGGING_INTERCEPTOR_KEY)) {
        HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
    }

    single(named(ACCEPT_HEADER_INJECTOR)) {
        return@single Interceptor { chain ->
            val newRequest = chain.request()
                .newBuilder()
                .addHeader("Accept", "application/json")
                .build()

            return@Interceptor chain.proceed(newRequest)
        }
    }

    factory(named (AUTH_INTERCEPTOR)) {
        val auth: Auth = get()
        Log.e("Auth token",auth.accessToken)
        return@factory Interceptor { chain ->
            val newRequest = chain.request()
                    .newBuilder()
                    .addHeader("Authorization", "Bearer ${auth.accessToken}")
                    .build()

            return@Interceptor chain.proceed(newRequest)
        }
    }

    single(named(UNAUTHENTICATED_RETROFIT)) {
        // retrofit builder
        val builder = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .addCallAdapterFactory(SimpleAdapterFactory.create())

        // OkHttpClient builder
        val clientBuilder: OkHttpClient.Builder = get()

        // add logging Interceptor
        val loggingInterceptor: HttpLoggingInterceptor = get(named(LOGGING_INTERCEPTOR_KEY))
        clientBuilder.addInterceptor(loggingInterceptor)

        // accept header injector
        clientBuilder.addInterceptor(get<Interceptor>(named(ACCEPT_HEADER_INJECTOR)))


        val client = clientBuilder.build()
        builder.client(client)

        return@single builder
    }

    single(named(AUTHENTICATED_RETROFIT)){
        // retrofit builder
        val builder = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .addCallAdapterFactory(SimpleAdapterFactory.create())

        // OkHttpClient builder
        val clientBuilder: OkHttpClient.Builder = get()

        // add logging Interceptor
        val loggingInterceptor: HttpLoggingInterceptor = get(named(LOGGING_INTERCEPTOR_KEY))
        clientBuilder.addInterceptor(loggingInterceptor)

        // accept header injector
        clientBuilder.addInterceptor(get<Interceptor>(named(ACCEPT_HEADER_INJECTOR)))

//        clientBuilder.addInterceptor(get(named(ACCEPT_HEADER_INJECTOR)))

        // add request header injector
//        val interceptor: Interceptor = get(named(AUTH_INTERCEPTOR))
//        clientBuilder.addInterceptor(interceptor)
        val interceptor: Interceptor = get<Interceptor>(named(AUTH_INTERCEPTOR))
        clientBuilder.addInterceptor(interceptor)

        val client = clientBuilder.build()
        builder.client(client)

        return@single builder.build()
    }

    single(named (UNAUTHENTICATED_HTTP_SERVICE)) {
        val retrofit: Retrofit.Builder = get(named(UNAUTHENTICATED_RETROFIT))
        return@single retrofit.build().create(HttpService::class.java)
    }

    single(named (AUTHENTICATED_HTTP_SERVICE)) {
        val retrofit: Retrofit = get(named(AUTHENTICATED_RETROFIT))
        return@single retrofit.create(HttpService::class.java)
    }
}

val appModules = listOf(appModule, networkModule)