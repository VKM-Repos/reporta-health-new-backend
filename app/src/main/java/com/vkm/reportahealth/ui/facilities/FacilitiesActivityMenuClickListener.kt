package com.vkm.reportahealth.ui.facilities

import android.content.Context
import android.content.Intent
import android.view.View
import android.widget.PopupMenu
import com.vkm.reportahealth.R
import com.vkm.reportahealth.ui.account.ProfileActivity
import com.vkm.reportahealth.ui.stats.StatsActivity

class FacilitiesActivityMenuClickListener(private val context: Context): View.OnClickListener {
    override fun onClick(v: View?) {
        val popUp = PopupMenu(context, v)
        popUp.inflate(R.menu.menu_facilities_activity)
        popUp.setOnMenuItemClickListener { item ->
            when(item?.itemId) {
                R.id.accountMenu -> context.startActivity(Intent(context, ProfileActivity::class.java))
                R.id.statsMenu -> context.startActivity(Intent(context, StatsActivity::class.java))
                else -> {}
            }
            return@setOnMenuItemClickListener true
        }
        popUp.show()
    }
}