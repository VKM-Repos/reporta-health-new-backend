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

class FacilitiesFilterAdapter(private var data: ArrayList<Facility>)
    : RecyclerView.Adapter<FacilitiesFilterAdapter.FacilityViewHolder>(), Filterable {

    // These explicit types (Facility) -> Unit fix the "Explicit type required" error
    var adapterClickEventListener: ((Facility) -> Unit)? = null
    var emptyDataNotifier: ((Boolean) -> Unit)? = null

    private var original = ArrayList(data)

    // This function must exist for the Activity to call it
    fun updateData(newData: ArrayList<Facility>) {
        original.clear()
        original.addAll(newData)
        this.data = ArrayList(newData)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
        FacilityViewHolder(LayoutInflater.from(parent.context).inflate(R.layout.layout_facility_search_result, parent, false))

    override fun getItemCount() = data.size

    override fun onBindViewHolder(holder: FacilityViewHolder, position: Int) = holder.bind(data[position])

    override fun getFilter(): Filter = namedFilter

    private val namedFilter = object: Filter() {
        override fun performFiltering(constraint: CharSequence?): FilterResults {
            val charString = constraint?.toString() ?: ""
            val filteredList = if (charString.isEmpty()) original else {
                val list = ArrayList<Facility>()
                for (item in original) {
                    if (item.name.contains(charString, true)) list.add(item)
                }
                list
            }
            return FilterResults().apply { values = filteredList }
        }

        @Suppress("UNCHECKED_CAST")
        override fun publishResults(constraint: CharSequence?, results: FilterResults?) {
            data = results?.values as ArrayList<Facility>
            emptyDataNotifier?.invoke(data.isNotEmpty())
            notifyDataSetChanged()
        }
    }

    inner class FacilityViewHolder(view: View): RecyclerView.ViewHolder(view) {
        private val nameTextView = view.findViewById<TextView>(R.id.facilityNameSearchResult)
        private val addressTextView = view.findViewById<TextView>(R.id.facilityAddressSearchResult)
        private val root = view.findViewById<LinearLayout>(R.id.facilitySearchResultItemRoot)

        fun bind(facility: Facility) {
            nameTextView.text = facility.name
            addressTextView.text = if (facility.postalAddress.isNotEmpty()) facility.postalAddress
            else "${facility.lganame}, ${facility.statename}"
            root.setOnClickListener { adapterClickEventListener?.invoke(facility) }
        }
    }
}