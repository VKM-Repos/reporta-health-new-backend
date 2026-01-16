package com.vkm.reportahealth.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.FacilityType

class FacilityTypeAdapter(private val facilitiesType: List<FacilityType>): RecyclerView.Adapter<FacilityTypeAdapter.FacilityTypeHolder>() {

    // listener to report clicked facility type
    var clickListener: (FacilityType) -> Unit = {}

    override fun onBindViewHolder(holder: FacilityTypeHolder, position: Int) {
        val facilityType = facilitiesType[position]
        holder.bind(facilityType)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FacilityTypeHolder {
        val inflater = LayoutInflater.from(parent.context)
        return FacilityTypeHolder(inflater.inflate(R.layout.layout_facility, parent, false))
    }

    override fun getItemCount() = facilitiesType.size

    inner class FacilityTypeHolder(view: View): RecyclerView.ViewHolder(view) {
        private val nameTextView by lazy { view.findViewById<TextView>(R.id.facilityTypeText) }
        private val logoImage by lazy { view.findViewById<ImageView>(R.id.facilityTypeLogo) }
        private val root by lazy { view.findViewById<FrameLayout>(R.id.facilityTypeRoot) }

        fun bind(f: FacilityType) {
            nameTextView.text = f.title
            logoImage.setImageResource(f.icon)

            root.setOnClickListener {
                clickListener(facilitiesType[adapterPosition])
            }
        }
    }
}