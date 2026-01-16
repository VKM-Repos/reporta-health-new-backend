package com.vkm.reportahealth.ui.account

import android.content.SharedPreferences
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import com.vkm.reportahealth.R
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.utils.Cache
//import kotlinx.android.synthetic.main.activity_profile.*
//import net.steamcrafted.materialiconlib.MaterialMenuInflater
import org.koin.android.ext.android.inject

import android.widget.TextView
import android.view.MenuInflater
import com.vkm.reportahealth.databinding.ActivityProfileBinding



//class ProfileActivity : BaseActivity() {
//    private lateinit var binding: ActivityProfileBinding
//    private val pref: SharedPreferences by inject()
//    override fun onCreate(savedInstanceState: Bundle?) {
//        super.onCreate(savedInstanceState)
//        binding = ActivityProfileBinding.inflate(layoutInflater)
//        setContentView(binding.root)
//        setContentView(R.layout.activity_profile)
//
//        setupUI()
//    }
//
//    private fun setupUI() {
//        supportActionBar?.let {
//            it.title = "Profile"
//            it.setDisplayHomeAsUpEnabled(true)
//        }
//
//
//        val user = Cache.fetchCachedUser(pref)
//        user?.let {
//            binding.profileNameTextView.text = it.name
//            binding.profileEmailTextView.text = it.email
//            binding.profilePhoneNumberTextView.text = it.phone
//        }
//    }
//    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
//        // Replace 'binding' with the actual library object if it's not ViewBinding
//        // Ensure you have R.menu.menu_profile created in your res/menu folder
//
//        // Example of what it looks like if using a Menu Builder library:
//        /*
//        SomeMenuLibrary.with(this, menu)
//            .setDefaultColorResource(R.color.white)
//            .inflate(R.menu.menu_profile)
//        */
//
//        return super.onCreateOptionsMenu(menu)
//    }
////    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
////        menuInflater.inflate(R.menu.your_menu, menu)
////                binding.with(this, menuInflater)
////                binding.setDefaultColor(R.color.white)
////                .setDefaultColorResource(R.color.white)
////                .inflate(R.menu.menu_profile, menu)
////        return super.onCreateOptionsMenu(menu)
////    }
//
//
//    override fun onOptionsItemSelected(item: android.view.MenuItem): Boolean {
//        return when(item.itemId) {
//            R.id.menuEditProfile -> {
//                // Your edit profile logic here
//                true
//            }
//            android.R.id.home -> {
//                onBackPressed()
//                true
//            }
//            // Always call super for the 'else' case to allow system handling
//            else -> super.onOptionsItemSelected(item)
//        }
//    }
//
//private fun ActivityProfileBinding.with(
//    activity: ProfileActivity,
//    menuInflater: MenuInflater
//): ActivityProfileBinding {
//    return this
//}
class ProfileActivity : BaseActivity() {

    private lateinit var binding: ActivityProfileBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Correct way to initialize Binding
        binding = ActivityProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Profile"
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        // Inflate your menu here instead of inside a binding function
        menuInflater.inflate(R.menu.menu_profile, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.menuEditProfile -> {
                // Edit logic
                true
            }
            android.R.id.home -> {
                onBackPressed()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}