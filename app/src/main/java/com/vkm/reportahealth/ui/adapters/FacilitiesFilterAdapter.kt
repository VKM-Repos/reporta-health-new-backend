package com.vkm.reportahealth.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Filter
import android.widget.Filterable
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.utils.Logger

class FacilitiesFilterAdapter(private var data: ArrayList<Facility>)
    : RecyclerView.Adapter<FacilitiesFilterAdapter.FacilityViewHolder>(), Filterable {

    var emptyDataNotifier: (Boolean) -> Unit = {}
    var adapterClickEventListener: (Facility) -> Unit = {}
    private var original = data

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
        FacilityViewHolder(LayoutInflater.from(parent.context).inflate(R.layout.layout_facility_search_result, parent, false))

    override fun getItemCount() = data.size

    override fun onBindViewHolder(holder: FacilityViewHolder, position: Int) {
        holder.bind(data[position])
    }

    override fun getFilter(): Filter {
        return namedFilter
    }

    fun updateData(data: ArrayList<Facility>) {
        if (data.size > 0) {
            original.clear()
            data.forEach { original.add(it) }

            notifyDataSetChanged()
        }
    }

    private val namedFilter = object: Filter() {

        override fun performFiltering(constraint: CharSequence?): FilterResults {

            if (constraint != null && constraint.isNotEmpty()) {
                val filtered = filterFacilities(constraint.toString())
                val result = FilterResults()
                result.count = filtered.size
                result.values = filtered
                return result
            }

            return FilterResults().apply { count = 0 }
        }

        override fun publishResults(constraint: CharSequence?, results: FilterResults?) {

            val count = results?.count ?: 0
            if (count > 0) {
                data = results?.values as ArrayList<Facility>

                emptyDataNotifier(true)
                notifyDataSetChanged()
            }else {
                data = ArrayList()
                emptyDataNotifier(false)
                notifyDataSetChanged()
            }
        }
    }

    private fun filterFacilities(keyword: String): ArrayList<Facility> {

        val result = ArrayList<Facility>()
        original.forEach { item ->
            if(item.name?.startsWith(keyword) == true ||
                item.name?.endsWith(keyword) == true ||
                item.name?.contains(keyword, true) == true) { result.add(item) }
        }

        return result
    }
    inner class FacilityViewHolder(view: View): RecyclerView.ViewHolder(view) {

        private val nameTextView by lazy { view.findViewById<TextView>(R.id.facilityNameSearchResult) }
        private val addressTextView by lazy { view.findViewById<TextView>(R.id.facilityAddressSearchResult) }
        private val root by lazy { view.findViewById<LinearLayout>(R.id.facilitySearchResultItemRoot) }

        fun bind(facility: Facility) {
            nameTextView.text = facility.name
            addressTextView.text = if (facility.postalAddress.isNotEmpty()) facility.postalAddress
            else "${facility.lganame}, ${facility.statename}"

            root.setOnClickListener {
                adapterClickEventListener.invoke(facility)
            }
        }
    }
}