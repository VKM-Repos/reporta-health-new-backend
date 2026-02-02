package com.vkm.reportahealth.ui.dialogs

import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.Window
import androidx.fragment.app.DialogFragment
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.databinding.LayoutFacilityDetailsDialogBinding
import com.vkm.reportahealth.ui.directions.DirectionsActivity
import com.vkm.reportahealth.ui.facilities.FacilitiesActivity
import com.vkm.reportahealth.ui.facilities.FacilityReviewsActivity
import com.vkm.reportahealth.ui.facilities.SubmitFacilityActivity
import com.vkm.reportahealth.utils.underline
import org.parceler.Parcels

class FacilityDetailsDialog : DialogFragment() {

    private lateinit var facility: Facility

    // ViewBinding setup
    private var _binding: LayoutFacilityDetailsDialogBinding? = null
    private val binding get() = _binding!!

    companion object {
        fun newInstance(data: Facility): FacilityDetailsDialog {
            val dialog = FacilityDetailsDialog()
            val bundle = Bundle().apply {
                putParcelable(Facility.TAG, Parcels.wrap(data))
            }
            dialog.arguments = bundle
            return dialog
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = LayoutFacilityDetailsDialogBinding.inflate(inflater, container, false)

        dialog?.window?.apply {
            setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
            requestFeature(Window.FEATURE_NO_TITLE)
        }

        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bindAndSetupUI()
    }

    private fun bindAndSetupUI() {
        // Safe unwrap of arguments
        val parcel = arguments?.getParcelable<android.os.Parcelable>(Facility.TAG)
        facility = Parcels.unwrap(parcel)

        // All views now prefixed with 'binding.'
        binding.facilityNameFacilityDetails.text = facility.name
        binding.facilityAddressFacilityDetails.text = facility.postalAddress
        binding.facilityOwnerShipFacilityDetails.text = "-"
        binding.facilityRegistrationNoFacilityDetails.text = facility.cacReg

        binding.buttonGetDirections.setOnClickListener {
            val directionIntent = Intent(requireContext(), DirectionsActivity::class.java).apply {
                putExtra(Facility.TAG, Parcels.wrap(facility))
            }
            startActivity(directionIntent)
        }

        val text = getString(R.string.report_an_issue)
        binding.buttonReportIssues.text = text.underline()
        binding.buttonReportIssues.setOnClickListener {
            val reportIntent = Intent(requireContext(), SubmitFacilityActivity::class.java).apply {
                putExtra(FacilitiesActivity.SEARCH_BOX_VALUE_KEY, facility.name)
                putExtra(FacilitiesActivity.LOCATION_LON, facility.fetchLongitude())
                putExtra(FacilitiesActivity.LOCATION_LAT, facility.fetchLatitude())
            }
            startActivity(reportIntent)
        }

        binding.buttonViewReportsFacilityDetails.setOnClickListener {
            val startIntent = Intent(requireContext(), FacilityReviewsActivity::class.java).apply {
                putExtra(Facility.TAG, Parcels.wrap(facility))
            }
            startActivity(startIntent)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null // Clear binding to avoid memory leaks
    }
}