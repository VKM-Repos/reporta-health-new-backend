package com.vkm.reportahealth.ui.stats

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.StatData
import com.vkm.reportahealth.data.models.StatDataKey
import com.vkm.reportahealth.databinding.LayoutActivityStatsBinding
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.ui.facilities.FacilityListActivity
import com.vkm.reportahealth.utils.onTextChange
import org.koin.androidx.viewmodel.ext.android.viewModel
import org.parceler.Parcels

class StatsActivity : BaseActivity() {

    private lateinit var binding: LayoutActivityStatsBinding
    private val stats = ArrayList<StatData>()
    private val adapter by lazy { StatsAdapter(stats) }
    private val viewModel: StatsViewModel by viewModel()
    private var statData: StatData? = null
    private var isLgaMode: Boolean? = false

    companion object {
        const val LGA_MODE = "LgaMode"

        @JvmStatic
        fun startActivityInLgaMode(context: Context, data: StatData) {
            val startIntent = Intent(context, StatsActivity::class.java).apply {
                putExtra(StatDataKey, Parcels.wrap(data))
                putExtra(LGA_MODE, true)
            }
            context.startActivity(startIntent)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Initialize View Binding
        binding = LayoutActivityStatsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        supportActionBar?.title = "General Statistics"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        isLgaMode = intent?.getBooleanExtra(LGA_MODE, false)
        if (isLgaMode == true) {
            adapter.lgaMode = true
            statData = Parcels.unwrap(intent?.getParcelableExtra(StatDataKey))
            supportActionBar?.title = "${statData?.state} LGAs"
        }

        setupUI()
        bindLiveDataEvents()
    }

    private fun setupUI() {
        binding.rvStats.layoutManager = LinearLayoutManager(this)
        binding.rvStats.adapter = adapter

        adapter.clickListener = { item ->
            if (isLgaMode != true) {
                startActivity(Intent(this, FullStatsActivity::class.java).apply {
                    putExtra(StatDataKey, Parcels.wrap(item))
                })
            } else {
                startActivity(Intent(this, FacilityListActivity::class.java).apply {
                    putExtra("LGA_ID", item.lgaId)
                    putExtra("STATE_ID", statData?.stateId)
                    putExtra("LGA_NAME", item.lga)
                })
            }
        }

        binding.errorLayoutStats.setOnClickListener {
            if (isLgaMode == true) {
                viewModel.fetchFacilitiesByLga(statData?.stateId ?: "")
            } else {
                viewModel.fetchFacilitiesCountByState()
            }
        }

        binding.filterStatsEdittext.onTextChange { text ->
            adapter.filter.filter(text)
        }
    }

    private fun bindLiveDataEvents() {
        if (isLgaMode == true) {
            viewModel.fetchFacilitiesByLga(statData?.stateId ?: "")
        } else {
            viewModel.fetchFacilitiesCountByState()
        }

        viewModel.responseLiveData().observe(this, Observer { state ->
            when (state.state) {
                Resource.STATE_ERROR -> {
                    toast(state.message)
                    binding.pwStateStats.visibility = View.GONE
                    binding.errorLayoutStats.visibility = View.VISIBLE
                }
                Resource.STATE_LOADING -> {
                    binding.errorLayoutStats.visibility = View.GONE
                    binding.pwStateStats.visibility = View.VISIBLE
                }
                Resource.STATE_SUCCESS -> {
                    binding.errorLayoutStats.visibility = View.GONE
                    binding.pwStateStats.visibility = View.GONE
                    state.data?.let { adapter.updateData(it) }
                }
            }
        })
    }
}