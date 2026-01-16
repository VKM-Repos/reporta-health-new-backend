package com.vkm.reportahealth.ui.stats

import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.lifecycle.Observer
import com.github.mikephil.charting.charts.PieChart
import com.github.mikephil.charting.data.PieData
import com.github.mikephil.charting.data.PieDataSet
import com.github.mikephil.charting.data.PieEntry
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.StatData
import com.vkm.reportahealth.data.models.StatDataKey
import com.vkm.reportahealth.data.models.ViewData
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.utils.underline
import org.eazegraph.lib.charts.BarChart
import org.eazegraph.lib.models.BarModel
import org.koin.androidx.viewmodel.ext.android.viewModel
import org.parceler.Parcels
import java.util.*

class FullStatsActivity : BaseActivity() {
    private val viewModel: StatsViewModel by viewModel()

    private val barChart by lazy { findViewById<BarChart>(R.id.barChartStat) }
    private val pieViewLevelOfCare by lazy { findViewById<PieChart>(R.id.pieViewLevelOfCare) }
    private val pieViewByOwnerShip by lazy { findViewById<PieChart>(R.id.pieViewByOwnerShip) }
    private val locationTextView by lazy { findViewById<TextView>(R.id.locationTextView) }
    private val buttonViewLgaFacilities by lazy { findViewById<TextView>(R.id.buttonViewLgaFacilities) }

    private var statData: StatData? = StatData()

    companion object {
        val COLORS = arrayOf(R.color.chart_1, R.color.chart_2, R.color.chart_3, R.color.chart_4)
        val PIE_COLORS = arrayOf(R.color.chart_5, R.color.chart_6, R.color.chart_1, R.color.chart_2)
        val FACILITIES =
            arrayOf("Hospitals and Clinics", "Drug Stores", "Laboratories", "Imaging Centers")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.layout_full_stats)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        statData = Parcels.unwrap(intent?.getParcelableExtra(StatDataKey))
        supportActionBar?.title = "${statData?.state} Statistics"

        bindLiveDataEvents()
    }

    private fun setupUI(data: ViewData) {
        locationTextView.text = statData?.state

        // Bar Chart setup
        barChart.clearChart()
        barChart.addBar(
            BarModel(
                FACILITIES[0],
                data.facility_count!!.total_no_hospitals.toFloat(),
                ContextCompat.getColor(this, COLORS[0])
            )
        )
        barChart.addBar(
            BarModel(
                FACILITIES[1],
                data.facility_count!!.total_no_pharmacies.toFloat(),
                ContextCompat.getColor(this, COLORS[1])
            )
        )
        barChart.addBar(
            BarModel(
                FACILITIES[2],
                data.facility_count!!.total_no_labs.toFloat(),
                ContextCompat.getColor(this, COLORS[2])
            )
        )
        barChart.addBar(
            BarModel(
                FACILITIES[3],
                data.facility_count!!.total_no_imaging_fac.toFloat(),
                ContextCompat.getColor(this, COLORS[3])
            )
        )
        barChart.startAnimation()

        // Level of Care PieChart
        val careEntries = data.hospitalsByCare?.map {
            PieEntry(it.total.toFloat(), it.care_level?.level ?: "Unknown")
        } ?: emptyList()
        renderPieChart(pieViewLevelOfCare, careEntries, "Level of Care")

        // Ownership PieChart
        val ownershipEntries = data.hospitalsByOwnership?.map {
            PieEntry(it.total.toFloat(), it.ownership?.description ?: "Unknown")
        } ?: emptyList()
        renderPieChart(pieViewByOwnerShip, ownershipEntries, "Ownership")

        // LGA Button
        buttonViewLgaFacilities.text = getString(R.string.view_lgas).underline()
        buttonViewLgaFacilities.setOnClickListener {
            statData?.let { StatsActivity.startActivityInLgaMode(this, it) }
        }
    }

    private fun renderPieChart(pieChart: PieChart, entries: List<PieEntry>, label: String) {
        val dataSet = PieDataSet(entries, label)
        dataSet.colors = PIE_COLORS.map { ContextCompat.getColor(this, it) }
        dataSet.valueTextColor = Color.WHITE
        dataSet.valueTextSize = 12f

        val data = PieData(dataSet)
        pieChart.data = data
        pieChart.description.isEnabled = false
        pieChart.centerText = label
        pieChart.setEntryLabelColor(Color.BLACK)
        pieChart.animateY(1500)
        pieChart.invalidate()
    }

    private fun bindLiveDataEvents() {
        viewModel.fetchFacilitiesByLevels(statData!!.state)
        viewModel.facilityByLevels().observe(this, Observer { state ->
            when (state.state) {
                Resource.STATE_ERROR -> {
                    toast(state.message)
                }

                Resource.STATE_LOADING -> {
                    // Handle loading state
                }

                Resource.STATE_SUCCESS -> {
                    state.data?.let { setupUI(it) }
                }
            }
        })
    }
}