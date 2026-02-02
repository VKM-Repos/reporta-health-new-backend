package com.vkm.reportahealth.ui.facilities

import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.gms.maps.*
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.android.material.snackbar.Snackbar
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.data.models.FacilityType
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.adapters.FacilitiesFilterAdapter
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.dialogs.FacilityDetailsDialog
import com.vkm.reportahealth.utils.*
import org.koin.android.ext.android.inject
import org.parceler.Parcels
import com.vkm.reportahealth.databinding.ActivityFacilityListBinding

class FacilitiesActivity: BaseActivity(), OnMapReadyCallback {
    private lateinit var binding: ActivityFacilityListBinding

    companion object {
        private const val RC_PERMISSION = 11
        const val SEARCH_BOX_VALUE_KEY = "search_box_value_key"

        // ADD THESE TWO LINES - They fix the "Red" in FacilityDetailsDialog
        const val LOCATION_LAT = "location_latitude"
        const val LOCATION_LON = "location_longitude"
    }

    private val viewModel: FacilitiesViewModel by inject()
    private var facilities = ArrayList<Facility>()
    private var currentLocation: Location? = null
    private lateinit var facType: FacilityType



    override fun onResume() {
        super.onResume()
        Log.e("LIFE", "SplashActivity onResume")
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.e("LIFE", "SplashActivity onDestroy")
    }

    // FIXED: Explicitly added the type ': FacilitiesFilterAdapter' to stop the errors
    private val filterAdapter: FacilitiesFilterAdapter by lazy {
        FacilitiesFilterAdapter(facilities).apply {
            adapterClickEventListener = { item: Facility ->
                val dialog = FacilityDetailsDialog.newInstance(item)
                dialog.show(supportFragmentManager, "DetailsFragment")
            }
            emptyDataNotifier = { hasData: Boolean ->
                showData(hasData)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityFacilityListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val parcel = intent?.getParcelableExtra<android.os.Parcelable>(FacilityType.TAG)
        facType = Parcels.unwrap(parcel)

        setupUI()
        bindClickListeners()
        setupLiveDataEvents()
        Log.e("LIFE", "SplashActivity onCreate")

    }

    private fun setupUI() {
        val mapFragment = supportFragmentManager.findFragmentById(R.id.mapFragment) as SupportMapFragment
        mapFragment.getMapAsync(this)

        binding.rvFacilitiesSearchResult.layoutManager = LinearLayoutManager(this)
        binding.rvFacilitiesSearchResult.adapter = filterAdapter

        binding.filterFacilitiesEditText.onTextChange { newText ->
            viewModel.searchFacilities(newText.trim())
        }
    }

    private fun showData(hasData: Boolean) {
        binding.rvFacilitiesSearchResult.visibility = if (hasData) View.VISIBLE else View.GONE
        binding.loader.visibility = View.GONE

        val isQueryEmpty = binding.filterFacilitiesEditText.text.toString().isEmpty()

        if (!hasData && !isQueryEmpty) {
            binding.layoutNotFoundFacilityActivity.visibility = View.VISIBLE
        } else {
            binding.layoutNotFoundFacilityActivity.visibility = View.GONE
        }
    }

    private fun bindClickListeners() {
        binding.backButtonShowFacilities.setOnClickListener { finish() }

        binding.reportFacilityButton.setOnClickListener {
            val text = binding.filterFacilitiesEditText.text.toString().trim()
            startActivity(Intent(this, SubmitFacilityActivity::class.java).apply {
                putExtra(SEARCH_BOX_VALUE_KEY, text)
            })
        }
    }

    private fun setupLiveDataEvents() {
        viewModel.searchResultLiveData().observe(this, Observer { resource ->
            when(resource.state) {
                Resource.STATE_LOADING -> {
                    binding.loader.visibility = View.VISIBLE
                    binding.layoutNotFoundFacilityActivity.visibility = View.GONE
                }
                Resource.STATE_SUCCESS -> {
                    binding.loader.visibility = View.GONE
                    resource.data?.let {
                        // filterAdapter now correctly recognizes 'updateData'
                        filterAdapter.updateData(ArrayList(it))
                    }
                }
                Resource.STATE_ERROR -> {
                    binding.loader.visibility = View.GONE
                }
            }
        })
    }

    override fun onMapReady(googleMap: GoogleMap) {
        try {
            googleMap.isMyLocationEnabled = true
            googleMap.setMapStyle(MapStyleOptions.loadRawResourceStyle(this, R.raw.style_json))
        } catch (e: SecurityException) {}
    }
}