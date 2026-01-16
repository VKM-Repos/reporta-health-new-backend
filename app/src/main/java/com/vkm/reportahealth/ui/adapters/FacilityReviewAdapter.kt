package com.vkm.reportahealth.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.data.models.Review
//import kotlinx.android.synthetic.main.layout_report_header.view.*
import java.lang.IllegalStateException

class FacilityReviewAdapter(private val reviews: ArrayList<Review>):
        RecyclerView.Adapter<FacilityReviewAdapter.FacilityReviewViewHolder>() {

    private lateinit var facility: Facility
    companion object {
        const val TYPE_HEADER = 1
        const val TYPE_REVIEW = 2
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FacilityReviewViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return when(viewType) {
            TYPE_HEADER -> FacilityHeaderViewHolder(inflater.inflate(R.layout.layout_report_header, parent, false))
            TYPE_REVIEW -> ReviewViewHolder(inflater.inflate(R.layout.layout_report, parent, false))
            else -> throw IllegalStateException("Unrecognized view type $viewType")
        }
    }

    override fun getItemViewType(position: Int): Int {
        return if (position == 0) TYPE_HEADER else TYPE_REVIEW
    }

    override fun getItemCount() = reviews.size

    override fun onBindViewHolder(holder: FacilityReviewViewHolder, position: Int) {
        when(holder) {
            is ReviewViewHolder -> holder.bind(review = reviews[position])
            is FacilityHeaderViewHolder -> holder.bind(facility)
        }
    }

    fun setFacility(facility: Facility) {
        this.facility = facility
    }

    open inner class FacilityReviewViewHolder(view: View): RecyclerView.ViewHolder(view)

    inner class ReviewViewHolder(view: View): FacilityReviewViewHolder(view) {
        private val usernameTextView by lazy {
            view.findViewById<TextView>(R.id.usernameLayoutReport) }
        private val reportTimeTextView by lazy {
            view.findViewById<TextView>(R.id.reportTimeTextView) }
        private val reportText by lazy {
            view.findViewById<TextView>(R.id.reportText) }

        fun bind(review: Review) {
            usernameTextView.text = review.username
            reportTimeTextView.text = review.reportTime
            reportText.text = review.reportText
        }
    }

    inner class FacilityHeaderViewHolder(view: View): FacilityReviewViewHolder(view) {
        private val facilityNameTextView by lazy {
            view.findViewById<TextView>(R.id.facilityNameReportHeader) }
        private val facilityAddressTextView by lazy {
            view.findViewById<TextView>(R.id.facilityAddressReportHeader) }
        private val facilityRegNumberTextView by lazy {
            view.findViewById<TextView>(R.id.registrationNumberReportHeader) }

        fun bind(facility: Facility) {
            facilityNameTextView.text = facility.name
            facilityAddressTextView.text = facility.postalAddress
            facilityRegNumberTextView.text = facility.cacReg
        }
    }
}