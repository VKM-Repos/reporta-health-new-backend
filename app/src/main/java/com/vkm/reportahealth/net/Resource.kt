package com.vkm.reportahealth.net

class Resource<T> {

    companion object {
        const val STATE_LOADING = 1
        const val STATE_ERROR = 2
        const val STATE_SUCCESS = 3
    }

    var state = STATE_LOADING
    var message: String? = ""
    var data: T? = null
}