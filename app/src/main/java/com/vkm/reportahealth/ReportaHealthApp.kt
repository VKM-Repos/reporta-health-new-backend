package com.vkm.reportahealth

import androidx.multidex.MultiDexApplication
import com.vkm.reportahealth.di.appModules
import org.koin.android.ext.koin.androidContext // Import change
import org.koin.android.ext.koin.androidLogger  // Optional
import org.koin.core.context.startKoin         // Import change

class ReportaHealthApp : MultiDexApplication() {

    override fun onCreate() {
        super.onCreate()

        // Modern Koin Start Syntax
        startKoin {
            // Log Koin events (optional)
            androidLogger()
            // Reference Android context
            androidContext(this@ReportaHealthApp)
            // Load modules
            modules(appModules)
        }
    }
}