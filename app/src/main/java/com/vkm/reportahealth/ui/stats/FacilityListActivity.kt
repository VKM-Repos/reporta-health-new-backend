package com.vkm.reportahealth.ui.stats

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.adapters.FacilitiesListAdapter
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.stats.viewmodels.FacilityListViewModel
import com.vkm.reportahealth.utils.hide
import com.vkm.reportahealth.utils.show
import org.koin.android.ext.android.inject
import com.vkm.reportahealth.databinding.ActivityFacilityListBinding



class FacilityListActivity : BaseActivity() {
    private lateinit var binding: ActivityFacilityListBinding
    private var lgaName: String? =""
    companion object {
        const val LGA_ID = "lga_id"
        const val STATE_ID = "state_id"
        const val LGA_NAME = "lga_name"
    }


    private val facilities = ArrayList<Facility>()
    private val adapter by lazy { FacilitiesListAdapter(this,facilities) }
    private val viewModel: FacilityListViewModel by inject()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityFacilityListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val lgaId = intent.getStringExtra(LGA_ID)
        val stateId = intent.getStringExtra(STATE_ID)
        lgaName = intent.getStringExtra(LGA_NAME)

        supportActionBar?.title = "Facilities in $lgaName"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        binding.facilityList.layoutManager = LinearLayoutManager(this)
        binding.facilityList.adapter = adapter
        observeData()
        viewModel.loadFacilities(lgaId, stateId)

    }
    fun observeData() {
        viewModel.responseLiveData().observe(this, Observer { state ->
            when (state.state) {
                Resource.STATE_SUCCESS -> {
                    binding.progressWheelListFacilities.hide()
                    val data = state.data

                    data?.let {
                        if (it.isNotEmpty()) {
                            facilities.clear()
                            facilities.addAll(it)
                            binding.facilityList.show()
                            adapter.notifyDataSetChanged()
                        } else {
                            binding.facilityList.hide()
                            binding.errorMessageView.show()
                            binding.errorMessageView.text = "We couldn't find any facility around in $lgaName"
                        }
                    }
                }
                Resource.STATE_LOADING -> {
                    binding.progressWheelListFacilities.show()
                }
            }
        }
        )
        viewModel.errorLiveData().observe(this, Observer { msg ->
            binding.facilitiesListRecyclerView.visibility = View.GONE  // Replaces facilityList.hide()
            binding.progressWheelListFacilities.visibility = View.VISIBLE // Replaces show()
            binding.errorMessageView.visibility = View.VISIBLE // Replaces show()
            binding.errorMessageView.text = "Your error message here" // Replaces .te
        })
    }
}
