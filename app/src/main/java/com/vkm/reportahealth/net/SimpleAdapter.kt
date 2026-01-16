package com.vkm.reportahealth.net

import android.util.Log
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.google.gson.Gson
import retrofit2.Call
import retrofit2.CallAdapter
import retrofit2.Callback
import retrofit2.Response
import java.io.IOException
import java.lang.reflect.Type
import java.util.*

internal typealias SimpleResponseHandler<T> = (T, Throwable?) -> Unit

class Simple<R>(private val call: Call<R>) {

    fun process(responseHandler: SimpleResponseHandler<R?> ) {

        // define callback
        val callback = object : Callback<R> {
            override fun onFailure(call: Call<R>?, t: Throwable?) {
                if (call!!.isCanceled) {
                    Log.e("Network call", "On Cancelled " + t!!.message + ", " + (t is IOException))
                    return
                }
                Log.e("Network call", "On Failure " + t!!.message + ", " + (t is IOException))

                if (t is IOException) {
                    responseHandler(null, Throwable("Please check your internet connection"))
                } else {
                    responseHandler(null, Throwable("Error occurred! Please try again"))
                    FirebaseCrashlytics.getInstance().recordException(t)

                }
            }

            override fun onResponse(call: Call<R>?, response: Response<R>?) {
                val hasError = response?.code() in 400..505
                if (hasError) {
                    val error = response?.errorBody()?.string()
                    Log.e("Network call", "On Response with error " + error)

                    val message = error.also {
                        val responseMap = Gson().fromJson(it, HashMap::class.java) as HashMap<String, Any>
                        (responseMap["message"] as String)
                    }

                    responseHandler(null, Throwable(message))
                    return
                }
                responseHandler(response?.body(), null)
            }

        }

        // enqueue network call
        call.enqueue(callback)
    }

    fun cancel() {
        call.cancel()
    }
}


internal class SimpleCallAdapter<R>(private val responseType: Type) : CallAdapter<R, Any> {

    override fun responseType(): Type = responseType

    override fun adapt(call: Call<R>): Any = Simple(call)
}