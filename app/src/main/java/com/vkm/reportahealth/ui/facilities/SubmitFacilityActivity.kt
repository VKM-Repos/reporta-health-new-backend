package com.vkm.reportahealth.ui.facilities

import android.app.Activity
import android.app.ProgressDialog
import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.util.Log
import android.util.Patterns
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.core.content.ContextCompat
import androidx.lifecycle.Observer
import com.google.android.libraries.places.api.Places
import com.google.android.libraries.places.api.model.Place
import com.google.android.libraries.places.widget.Autocomplete
import com.google.android.libraries.places.widget.model.AutocompleteActivityMode
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.ReviewUser
import com.vkm.reportahealth.databinding.ActivityProfileBinding
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.ReportaEditText
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.utils.*
//import kotlinx.android.synthetic.main.layout_submit_report.*
import org.koin.android.ext.android.inject
import com.vkm.reportahealth.databinding.ActivitySubmitFacilityBinding


class SubmitFacilityActivity: BaseActivity() {
    private lateinit var binding: ActivitySubmitFacilityBinding
    companion object {
        val CATEGORIES = arrayOf("Hospitals and Clinics", "Drug Stores", "Laboratories", "Imaging Centers")
        val RC_SELECT_LOCATION = 15
    }

    private var selectedCategory = 0
    private var selectedLocationAddress = ""
    private var selectedPlace: Place? = null

    private val logger = Logger.with("SubmitReport")
    private val facilityNameEditText by lazy { findViewById<ReportaEditText>(R.id.facilityNameEdittText) }
    private val facilityLocationTextView by lazy { findViewById<TextView>(R.id.facilityLocationTextView) }
    private val facilityCategoryTextView by lazy { findViewById<TextView>(R.id.facilityCategoryTextView) }
    private val complaintEditText by lazy { findViewById<ReportaEditText>(R.id.complaintEditText) }
    private val nameEditText by lazy { findViewById<ReportaEditText>(R.id.nameEditText) }
    private val emailEditText by lazy { findViewById<ReportaEditText>(R.id.emailEditText) }
    private val phoneEditText by lazy { findViewById<ReportaEditText>(R.id.phoneEditText) }

    private val dialog by lazy { ProgressDialog(this).apply { setMessage("Processing...") } }
    private val viewModel: SubmitFacilityViewModel by inject()
    private val pref: SharedPreferences by inject()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySubmitFacilityBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setContentView(R.layout.layout_submit_report)

        supportActionBar?.title = "Submit Form"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        setupUI()
        handleLiveDataEvents()
    }

    private fun setupUI() {
        val preText = intent?.getStringExtra(FacilitiesActivity.SEARCH_BOX_VALUE_KEY) ?: ""
        val locLat = intent?.getDoubleExtra(FacilitiesActivity.LOCATION_LAT, 0.0)
        val locLon = intent?.getDoubleExtra(FacilitiesActivity.LOCATION_LON, 0.0)

        viewModel.fetchCurrentLocationAddress(LocationHelper.LocalLocation(locLat!!, locLon!!))

        facilityNameEditText.setGravity(ReportaEditText.GRAVTTY_CENTER)
        facilityNameEditText.setHint("Facility Name")
        facilityNameEditText.getEdiText().append(preText) // sets text and also moves cursor to the end of the text

        complaintEditText.setGravity(ReportaEditText.GRAVITY_TOP)
        complaintEditText.setHint("Complaint Field")

        nameEditText.setGravity(ReportaEditText.GRAVTTY_CENTER)
        nameEditText.setHint("Name")

        emailEditText.setGravity(ReportaEditText.GRAVTTY_CENTER)
        emailEditText.setHint("Email")

        phoneEditText.setGravity(ReportaEditText.GRAVTTY_CENTER)
        phoneEditText.setHint("Phone No")

        facilityLocationTextView.onTextChanged { newText ->
            if (!newText.isEmpty()) {
                binding.categoryErrorView.visibility = View.GONE
                facilityCategoryTextView.setTextColor(ContextCompat.getColor(this, R.color.textColorSecondary))
            }
        }

        bindClickEvents()

        val user = Cache.fetchCachedUser(pref)
        user?.let {
            nameEditText.setText(it.name)
            emailEditText.setText(it.email)
            phoneEditText.setText(it.phone)
        }
    }

    private fun bindClickEvents() {
        binding.submitReportButton.setOnClickListener {
            validateInputAndSubmit()
        }

        binding.selectLocationButton.setOnClickListener {
            openPlaceAutoComplete()
        }

        binding.selectCategoryButton.setOnClickListener {
            showSelectCategoryDialog()
        }
    }

    private fun validateInputAndSubmit() {
        var error = ""
        val name = facilityNameEditText.getText()
        val complaint = complaintEditText.getText()
        val userName = nameEditText.getText()
        val userEmail = emailEditText.getText()
        val userPhone = phoneEditText.getText()

        if (name.isBlank()) {
            facilityNameEditText.indicateError("Enter facility name")
            error = "Enter Facility Name"
        }

        if (complaint.isBlank()) {
            complaintEditText.indicateError("This field is required")
            error = "Complaint Field"
        }

        if (userEmail.isNotBlank()) {
            if (!Patterns.EMAIL_ADDRESS.matcher(userEmail.trim()).matches()) {
                emailEditText.indicateError("Enter a valid email address")
                error = "Email Error"
            }
            if (error != "") return
        }


        if (selectedCategory == 0) {
            binding.categoryErrorView.visibility = View.VISIBLE
            facilityCategoryTextView.text = "Please select a category"
            facilityCategoryTextView.setTextColor(ContextCompat.getColor(this, R.color.red))
            error = "Select Category Error"
        } else { binding.categoryErrorView.visibility = View.GONE; error = "" }

        hideKeyboard()
        if (error == "") {
            if(selectedLocationAddress == "") { selectedLocationAddress = "21 street, 9th avenue. apapa lagos" }
            viewModel.submitFacility(facilityName = name,
                facilityCategory = selectedCategory, location = selectedLocationAddress, name = userName,
                email = userEmail, phone = userPhone)

            val user = ReviewUser(userName, userEmail, userPhone)
            Cache.cacheReviewUser(pref, user)
        }else { /*fields are missing*/ }
    }


    private fun showSelectCategoryDialog() {
        val dialog = AlertDialog.Builder(this)
                .setTitle("Select Category")
                .setItems(CATEGORIES) { dialog, which ->
                    selectedCategory = which//CATEGORIES[which]
                    facilityCategoryTextView.text = CATEGORIES[which]

                    binding.categoryErrorView.visibility = View.GONE
                    facilityCategoryTextView.setTextColor(ContextCompat.getColor(this, R.color.textColorSecondary))
                    dialog.dismiss()
                }.create()
        dialog.show()
    }


    private fun openPlaceAutoComplete() {
        // Initialize Places.
        Places.initialize(applicationContext, getString(R.string.google_maps_key))

// Create a new Places client instance.
        val placesClient = Places.createClient(this)
        val autocompleteIntent = Autocomplete.IntentBuilder(
            AutocompleteActivityMode.FULLSCREEN,
            mutableListOf(Place.Field.ID, Place.Field.NAME, Place.Field.ADDRESS, Place.Field.LAT_LNG)
        )
            //  .setInitialQuery(getQuery())
            // .setHint(getHint())
            .setCountry("NG")
            // .setLocationBias(getLocationBias())
            // .setLocationRestriction(getLocationRestriction())
            // .setTypeFilter(getTypeFilter())
            .build(this)
        startActivityForResult(autocompleteIntent, RC_SELECT_LOCATION)

        /* val placeIntent = PlaceAutocomplete.IntentBuilder(PlaceAutocomplete.MODE_OVERLAY)
             .setFilter(AutocompleteFilter.Builder().setCountry("NG").build()).build(this)
         startActivityForResult(placeIntent, RC_SELECT_LOCATION)*/
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != RC_SELECT_LOCATION) return
        if (resultCode != Activity.RESULT_OK) return
        if (data == null) return

        selectedPlace = Autocomplete.getPlaceFromIntent(data)

        selectedLocationAddress = selectedPlace?.address.toString()

        facilityLocationTextView.text = selectedLocationAddress
    }

    private fun handleLiveDataEvents() {
        viewModel.liveData().observe(this, Observer { data ->
            when(data.state) {
                Resource.STATE_SUCCESS -> {
                    dialog.cancel()
                    data.data?.let {
                        toast(it.message )
                    if (it.isSuccess()) finish()
                    }
                }
                Resource.STATE_LOADING -> { dialog.show() }
                Resource.STATE_ERROR -> { dialog.cancel(); data.message?.let { toast(it) } }
            }
        })

        viewModel.locationAddressLiveData().observe(this, Observer { currentAddress ->
            when(currentAddress) {
                "" -> {
                    // error
                } else -> {
                    selectedLocationAddress = currentAddress
                    facilityLocationTextView.text = selectedLocationAddress
                }
            }
        })
    }
}
