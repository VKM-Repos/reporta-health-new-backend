package com.vkm.reportahealth.ui.adapters

import android.content.Context
import android.graphics.PorterDuff
import android.graphics.PorterDuffColorFilter
import android.graphics.drawable.Drawable
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.RelativeLayout
import android.widget.TextView
import androidx.annotation.ColorRes
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.utils.capitalizeWords

class FacilitiesListAdapter(val context: Context, private val data: ArrayList<Facility>) :
    RecyclerView.Adapter<FacilitiesListAdapter.FacilitiesViewHolder>() {

    var adapterClickEventListener: (Facility) -> Unit = {}

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FacilitiesViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return FacilitiesViewHolder(inflater.inflate(R.layout.facility_list_item, parent, false))
    }

    override fun getItemCount() = data.size

    override fun onBindViewHolder(holder: FacilitiesViewHolder, position: Int) {
        holder.bind(data[position])
    }

    inner class FacilitiesViewHolder(view: View): RecyclerView.ViewHolder(view) {

        private val facilityNameTextView by lazy { view.findViewById<TextView>(R.id.facilityNameTextView) }
        private val facilityAddressTextView by lazy { view.findViewById<TextView>(R.id.facilityAddressTextView) }
        private val facilityImageView by lazy { view.findViewById<ImageView>(R.id.facilityIconFacilityListItem) }
        private val root by lazy { view.findViewById<RelativeLayout>(R.id.rootFacilityLists) }

        fun bind(facility: Facility) {
            facilityNameTextView.text = facility.name.lowercase().capitalizeWords()
            facilityAddressTextView.text = if (facility.postalAddress.isNotEmpty()) facility.postalAddress
            else "${facility.lganame}, ${facility.statename}"
            when (facility.facilityType) {
                1 -> facilityImageView.setImageDrawable(ContextCompat.getDrawable(context, R.drawable.caduceus))
                2 -> facilityImageView.setImageDrawable(ContextCompat.getDrawable(context, R.drawable.drug_stores))
                3 -> facilityImageView.setImageDrawable(ContextCompat.getDrawable(context, R.drawable.labs))
                4 -> facilityImageView.setImageDrawable(
                    ContextCompat.getDrawable(context, R.drawable.imaging_center_png)
                )
            }
            facilityImageView.drawable.tint(context, R.color.colorPrimary)
            root.setOnClickListener {
                adapterClickEventListener(data[adapterPosition])
            }
        }
    }
}

fun Drawable.tint(context: Context, @ColorRes color: Int): Drawable {
    mutate()
    this.colorFilter = PorterDuffColorFilter(ContextCompat.getColor(context, color), PorterDuff.Mode.SRC_IN)
    return this
}