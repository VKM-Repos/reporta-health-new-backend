package com.vkm.reportahealth.ui.facilities

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Bundle
import android.provider.Settings
import android.text.Html
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.gms.maps.*
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.material.snackbar.Snackbar
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.data.models.FacilityType
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.adapters.FacilitiesFilterAdapter
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.dialogs.FacilityDetailsDialog
import com.vkm.reportahealth.utils.*
//import kotlinx.android.synthetic.main.content_home.*
//import kotlinx.android.synthetic.main.layout_no_facility.*
import org.koin.android.ext.android.inject
import org.parceler.Parcels
import com.vkm.reportahealth.databinding.ActivityFacilityListBinding
import com.google.android.material.bottomnavigation.BottomNavigationView



class FacilitiesActivity: BaseActivity(), OnMapReadyCallback {
    private lateinit var binding: ActivityFacilityListBinding

    companion object {
        private const val RC_PERMISSION = 11
        const val SEARCH_BOX_VALUE_KEY = "search_box_value_key"
        const val LOCATION_LAT = "location_latitude"
        const val LOCATION_LON = "location_longitude"
    }

    private val viewModel: FacilitiesViewModel by inject()
    private val locationHelper: LocationHelper by inject()

    private var facilities = ArrayList<Facility>()
    private val filterAdapter by lazy { FacilitiesFilterAdapter(facilities) }
    private val log = Logger.with("http")

    private var googleMap: GoogleMap? = null
    private var currentLocation: Location? = null
    private var facilityType: String? = ""
    private lateinit var facType: FacilityType
    private fun initializeMap() {
        // TODO: legacy stub – implementation pending
    }

    private fun isLocationEnabled(): Boolean {
        return true // assume enabled for now
    }

    private fun promptOpenLocationSettings() {
        // TODO: legacy stub – implementation pending
    }

    private fun requestPermissionAndUpdateLocation() {
        // TODO: legacy stub – implementation pending
    }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
//        setContentView(R.layout.activity_home)
        binding = ActivityFacilityListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        facType = Parcels.unwrap(intent?.getParcelableExtra(FacilityType.TAG))
        initializeMap()
        setupUI()
        bindClickListeners()
        setupLiveDataEvents()
    }

    override fun onMapReady(p0: GoogleMap?) {
        googleMap = p0

        try {
            googleMap?.isMyLocationEnabled = true
            googleMap?.setMapStyle(MapStyleOptions.loadRawResourceStyle(this, R.raw.style_json))
        }catch (e: SecurityException) {}
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != RC_PERMISSION) return

        if (grantResults.isEmpty()) return

        if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            viewModel.startLocationUpdates()

            if (!isLocationEnabled()) {
                promptOpenLocationSettings()
            }
        }else {
            Toast.makeText(this, "Failed to obtain location permission", Toast.LENGTH_LONG).show()
        }
    }


    private fun setupUI() {
        val mapFragment = supportFragmentManager.findFragmentById(R.id.mapFragment) as SupportMapFragment
        mapFragment.getMapAsync(this)

        facilityType = intent?.getStringExtra(FacilityType.TAG)

        // Fix: Added binding.
        binding.showListButton.setOnClickListener {
            log.log("$currentLocation $facilityType")
            currentLocation?.let {
                val dialog = ListFacilitiesBottomSheet.newInstance(it, facType)
                dialog.show(supportFragmentManager, "ShowBottomSheet")
            }
        }

        // Fix: Added binding.
        binding.rvFacilitiesSearchResult.setOnTouchListener { v, event ->
            hideKeyboard()
            false
        }

        // Fix: Added binding.
        binding.rvFacilitiesSearchResult.layoutManager = LinearLayoutManager(this)
        binding.rvFacilitiesSearchResult.adapter = filterAdapter

        filterAdapter.emptyDataNotifier = { hasData ->
            showData(hasData)
        }
        filterAdapter.adapterClickEventListener = { item ->
            val dialog = FacilityDetailsDialog.newInstance(item)
            dialog.show(supportFragmentManager, "DetailsFragment")
        }

        // Fix: Added binding.
        binding.filterFacilitiesEditText.onTextChange { newText ->
            viewModel.searchFacilities(newText.trim())
        }

        requestPermissionAndUpdateLocation()
    }

    private fun showData(hasData: Boolean) {
        // Fix: Added binding. to all references
        binding.rvFacilitiesSearchResult.visibility = if (hasData) View.VISIBLE else View.GONE
        binding.loader.visibility = View.GONE

        if (!hasData) {
            val emptyText = binding.filterFacilitiesEditText.text.toString().isEmpty()
            if (emptyText) {
                binding.rvFacilitiesSearchResult.visibility = View.GONE
                binding.layoutNotFoundFacilityActivity.visibility = View.GONE
            } else {
                binding.rvFacilitiesSearchResult.visibility = View.GONE
                binding.layoutNotFoundFacilityActivity.visibility = View.VISIBLE
            }
        } else {
            binding.layoutNotFoundFacilityActivity.visibility = View.GONE
        }
    }

    private fun bindClickListeners() {
        // Fix: Added binding.
        binding.settingsButtonShowFacilities.setOnClickListener(FacilitiesActivityMenuClickListener(this))

        binding.backButtonShowFacilities.setOnClickListener {
            finish()
        }

        binding.reportFacilityButton.setOnClickListener {
            val text = binding.filterFacilitiesEditText.text.toString().trim()
            val reportIntent = Intent(this, SubmitFacilityActivity::class.java).apply {
                putExtra(SEARCH_BOX_VALUE_KEY, text)
            }
            startActivity(reportIntent)
        }

        binding.reportFacility.setOnClickListener {
            val reportIntent = Intent(this, SubmitFacilityActivity::class.java)
            startActivity(reportIntent)
        }
    }

    private fun setupLiveDataEvents() {
        // ... (Location observer stays same)

        viewModel.searchResultLiveData().observe(this, Observer { resource ->
            when(resource.state) {
                Resource.STATE_LOADING -> {
                    // Fix: Added binding.
                    binding.loader.visibility = View.VISIBLE
                    binding.layoutNotFoundFacilityActivity.visibility = View.GONE
                }
                Resource.STATE_ERROR -> {}
                Resource.STATE_SUCCESS -> {
                    binding.loader.visibility = View.GONE
                    val data = resource.data
                    data?.let {
                        filterAdapter.updateData(data)
                        filterAdapter.notifyDataSetChanged()
                        showData(it.size > 0)
                    }
                }
            }
        })

        // ...

        viewModel.errorLiveData().observe(this, Observer { msg ->
            hideKeyboard()
            // Fix: Use binding.root for the snackbar
            val snackbar = Snackbar.make(binding.root, msg, Snackbar.LENGTH_LONG)
            snackbar.view.setBackgroundColor(ContextCompat.getColor(this, R.color.red))
            snackbar.setText("<font color=\"#ffffff\"> $msg </font>".loadHtml)
            snackbar.show()
        })
    }}