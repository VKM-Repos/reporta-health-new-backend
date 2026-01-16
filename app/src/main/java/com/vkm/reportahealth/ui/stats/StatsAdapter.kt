package com.vkm.reportahealth.ui.stats

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Filter
import android.widget.Filterable
import android.widget.RelativeLayout
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.StatData

class StatsAdapter(private var data: ArrayList<StatData>, var lgaMode: Boolean = false):
        RecyclerView.Adapter<StatsAdapter.StatsViewHolder>(), Filterable {
    override fun getFilter() = namedFilter
    var clickListener: (StatData) -> Unit = {}
    private var originalData = ArrayList<StatData>()

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): StatsViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return StatsViewHolder(inflater.inflate(R.layout.layout_stat, parent, false))
    }

    fun updateData(data: ArrayList<StatData>) {
        this.data = data
        originalData = data
        notifyDataSetChanged()
    }

    override fun getItemCount() = data.size

    override fun onBindViewHolder(holder: StatsViewHolder, position: Int) {
        val next = data[position]
        holder.bind(next)
    }

    inner class StatsViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        private val root by lazy { view.findViewById<RelativeLayout>(R.id.stat_root) }
        private val stateNameTextView by lazy { view.findViewById<TextView>(R.id.locationTextViewStats) }
        private val hospitalCountTextView by lazy { view.findViewById<TextView>(R.id.hospitalStatCount) }
        private val labsCountTextView by lazy { view.findViewById<TextView>(R.id.labStatCount) }
        private val drugStoresCountTextView by lazy { view.findViewById<TextView>(R.id.drugStoreStatCount) }
        private val imagingCenterCountTextView by lazy { view.findViewById<TextView>(R.id.imagingCentersStatCount) }
        private val viewMoreLabel by lazy { view.findViewById<TextView>(R.id.viewDetailsButton) }

        fun bind(data: StatData) {
            stateNameTextView.text = if (lgaMode) data.lga else data.state
            hospitalCountTextView.text = "${data.hospitalCount}"
            labsCountTextView.text = "${data.labCount}"
            drugStoresCountTextView.text = "${data.pharmacyCount}"
            imagingCenterCountTextView.text = "${data.imagingCenterCount}"
            viewMoreLabel.visibility = if (lgaMode) View.GONE else View.VISIBLE

            root.setOnClickListener { clickListener(data) }
        }
    }

    private val namedFilter = object: Filter() {
        override fun performFiltering(constraint: CharSequence?): FilterResults {
            val filtered = filterStats(constraint)
            val count = filtered.size
            val result = FilterResults()

            result.values = filtered
            result.count = count
            return result
        }

        override fun publishResults(constraint: CharSequence?, results: FilterResults?) {
            val count = results?.count ?: 0
            if (count > 0) {
                val values = results?.values as ArrayList<StatData>
                data = values
                notifyDataSetChanged()
            } else {
                data.clear()
                notifyDataSetChanged()
            }
        }
    }

    private fun filterStats(param: CharSequence?): ArrayList<StatData> {
        if (param == null || param.isEmpty()) return originalData

        val word = param.toString().lowercase()
        val result = ArrayList<StatData>()
        this.data.forEach {
            if (it.state.lowercase().startsWith(word) || it.lga.lowercase().startsWith(word)) {
                result.add(it)
            }
        }

        return result
    }
}