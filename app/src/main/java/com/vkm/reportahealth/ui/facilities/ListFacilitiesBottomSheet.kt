package com.vkm.reportahealth.ui.facilities

import android.location.Location
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.lifecycle.Observer
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.data.models.FacilityType
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.adapters.FacilitiesListAdapter
import com.vkm.reportahealth.ui.dialogs.FacilityDetailsDialog
import org.parceler.Parcels
import com.vkm.reportahealth.databinding.FacilityListBottomSheetBinding
import kotlinx.coroutines.launch
import kotlin.properties.ReadOnlyProperty



//
private val viewModel: FacilitiesViewModel by viewModel()

private fun viewModel(): ReadOnlyProperty<Any?, FacilitiesViewModel> =
    viewModel()

class ListFacilitiesBottomSheet: BottomSheetDialogFragment() {
    private lateinit var currentLocation: Location
    private lateinit var binding: FacilityListBottomSheetBinding
    private val facilities = ArrayList<Facility>()
//    private val adapter by lazy { FacilitiesListAdapter(this.context!!,facilities) } -
    private val adapter by lazy {
    FacilitiesListAdapter(requireContext(), facilities)
    }


    fun setup() {
        // initialize here
    }
    lateinit var facilityType: FacilityType

    private var _binding: FacilityListBottomSheetBinding? = null

    companion object {

        fun newInstance(location: Location, facilityType: FacilityType): ListFacilitiesBottomSheet {

            val bundle = Bundle().apply {
                putParcelable(Facility.TAG, location)
                putParcelable("FType", Parcels.wrap(facilityType))
            }

            return ListFacilitiesBottomSheet().apply { arguments = bundle }
        }
    }



    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // 1. Use the 'inflater' from the parameter
        // 2. Pass 'container' and 'false' so the view is sized correctly
        _binding = FacilityListBottomSheetBinding.inflate(inflater, container, false)

        // 3. Return the root view (Do NOT use setContentView)
        return binding.root
    }



    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        bindAndSetupUI()
        bindLiveDataEvents()
    }

    private fun bindAndSetupUI() {

        binding.facilitiesListRecyclerView.layoutManager = LinearLayoutManager(requireActivity())
        binding.facilitiesListRecyclerView.adapter = adapter

        currentLocation = arguments?.getParcelable<Location>(Facility.TAG)!!
        facilityType = Parcels.unwrap<FacilityType>(arguments?.getParcelable("FType"))

        adapter.adapterClickEventListener = { facility ->
            val dialog = FacilityDetailsDialog.newInstance(facility)
            dialog.show(childFragmentManager, "DetailsFragment")
        }

        binding.bottomSheetTitle.text = "${facilityType.title} around you"
        lifecycleScope.launch {
            viewModel.loadFacilities(currentLocation, facilityType.id)
            

        }

        binding.errorLayoutListFacilities.setOnClickListener {
            binding.dataLayout.visibility = View.VISIBLE
            binding.errorLayoutListFacilities.visibility = View.GONE
            lifecycleScope.launch {
                viewModel.loadFacilities(currentLocation, facilityType.id)

            }

        }
    }

    fun bindLiveDataEvents() {
        viewModel.facilitiesLiveData().observe(this, Observer { resource ->
            when(resource.state) {
                Resource.STATE_SUCCESS -> {
                    binding.progressWheelListFacilities.visibility = View.GONE
                    val data = resource.data
                    data?.let {
                        if (it.isNotEmpty()) {
                            facilities.clear()
                            facilities.addAll(it)
                            adapter.notifyDataSetChanged()
                        } else {
                           binding.dataLayout.visibility = View.GONE
                            binding.errorLayoutListFacilities.visibility = View.VISIBLE
                            binding.errorMessageView.text = "We couldn't find any ${facilityType.title} around you"
                        }
                    }
                }
                Resource.STATE_LOADING -> {
                    binding.progressWheelListFacilities.visibility = View.VISIBLE
                }
            }
        })

        viewModel.errorLiveData().observe(this, Observer { msg ->
            binding.dataLayout.visibility = View.GONE
            binding.progressWheelListFacilities.visibility = View.GONE
            binding.errorLayoutListFacilities.visibility = View.VISIBLE
            binding.errorMessageView.text = msg
        })
    }
}