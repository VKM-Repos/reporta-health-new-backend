package com.vkm.reportahealth.utils

/**
 * Author: Omolara Adejuwon
 * Date: 03/12/2018.
 */
class AppConstants {
    companion object {
        const val DB_NAME = "befit_fitness.db"
        const val KEY_DRIVER_UPDATE_KM = 1
        const val KEY_WORKER_DRIVER_ID = "driverId"
        const val KEY_WORKER_LAT = "lat"
        const val KEY_WORKER_LONG = "long"
    }

    class DeliveryStatus {
        companion object {
            const val COMPLETED = "COMPLETED"
            const val PENDING = "PENDING"
            const val IN_PROGRESS = "IN PROGRESS"
            const val REJECTED = "REJECTED"
            const val CANCELLED = "CANCELED"
            const val PICKED_UP = "PICKED UP"
            const val DROPPED_OFF = "DROPPED OFF"
        }

    }

}
