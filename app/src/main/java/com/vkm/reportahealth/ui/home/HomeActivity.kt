package com.vkm.reportahealth.ui.home

import android.content.Intent
import android.os.Bundle
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.FacilityType
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.facilities.FacilitiesActivity
//import kotlinx.android.synthetic.main.activity_select_facility.*
import org.parceler.Parcels
import com.vkm.reportahealth.databinding.ActivityHomeBinding
import com.vkm.reportahealth.databinding.ActivityProfileBinding

class HomeActivity: BaseActivity() {
    private lateinit var binding: ActivityHomeBinding
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setContentView(R.layout.activity_select_facility)

        setupUI()
    }

    private fun setupUI() {

        binding.buttonDrugStores.setOnClickListener {
            startFacilityActivity(FacilityType(0, "Drug Stores", 2))
        }

        binding.buttonLabs.setOnClickListener {
            startFacilityActivity(FacilityType(0, "Laboratories", 3))
        }

        binding.buttonHospitalsAndClinics.setOnClickListener {
            startFacilityActivity(FacilityType(0, "Hospitals And Clinics", 1))
        }

        binding.buttonImagingCenters.setOnClickListener {
            startFacilityActivity(FacilityType(0, "Imaging Center", 4))
        }
    }

    private fun startFacilityActivity(type: FacilityType) {
        val facilityActivityIntent = Intent(this, FacilitiesActivity::class.java).apply {
            putExtra(FacilityType.TAG, Parcels.wrap(type))
        }
        startActivity(facilityActivityIntent)
    }
}