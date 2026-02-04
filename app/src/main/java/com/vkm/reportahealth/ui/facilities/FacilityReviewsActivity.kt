package com.vkm.reportahealth.ui.facilities

import android.app.ProgressDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.data.models.Review
import com.vkm.reportahealth.net.Resource
import com.vkm.reportahealth.ui.adapters.FacilityReviewAdapter
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.utils.Logger
import org.koin.android.ext.android.inject
import kotlinx.coroutines.launch
import org.parceler.Parcels
import java.util.*
import com.vkm.reportahealth.databinding.LayoutAddReviewBinding



class FacilityReviewsActivity: BaseActivity() {

    private lateinit var facility: Facility
    private val reviews = ArrayList<Review>()
    private val adapter by lazy { FacilityReviewAdapter(reviews) }
    private val viewModel: FacilityReviewViewModel by inject()
    private val dialog by lazy { ProgressDialog(this).apply {
        setMessage("Submitting review...")
    } }
    private var prevText = ""

    private val refreshLayout by lazy { findViewById<SwipeRefreshLayout>(R.id.reviewsRoot) }
    private val errorTitle by lazy { findViewById<TextView>(R.id.errorTitle) }
    private val errorBody by lazy { findViewById<TextView>(R.id.errorBody) }
    private val errorLayout by lazy { findViewById<LinearLayout>(R.id.errorLayoutReviews) }

    private val logger = Logger.with("Reviews")

    private lateinit var binding: LayoutAddReviewBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(binding.root)

        // 1. First, get the data from the intent
        facility = Parcels.unwrap(intent?.getParcelableExtra(Facility.TAG))

        // 2. Now that 'facility' exists, you can use its ID
        lifecycleScope.launch {
            // Use facility.id (or whatever the ID field is named in your model)
            viewModel.fetchReviews(facility.id.toString())
        }

        // 3. Set up the rest of the UI
        binding.rvReports.layoutManager = LinearLayoutManager(this)
        binding.rvReports.adapter = adapter

        supportActionBar?.title = "Reviews"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        adapter.setFacility(facility)

        lifecycleScope.launch {
            setupUI()
        }
    }

    suspend fun setupUI() {
        adapter.setFacility(facility)
        binding.rvReports.layoutManager = LinearLayoutManager(this)
        binding.rvReports.adapter = adapter

        binding.submitViewFab.setOnClickListener {
            showSubmitReviewDialog()
        }


        loadReviews()

        refreshLayout.setOnRefreshListener {
            lifecycleScope.launch {
                viewModel.fetchReviews(facility.sigUniqueId)
            }
        }
    }

    private suspend fun loadReviews() {
        viewModel.fetchReviews(facility.sigUniqueId)
        viewModel.reviewLiveData().observe(this, androidx.lifecycle.Observer { resource ->
            when(resource.state) {
                Resource.STATE_LOADING -> { refreshLayout.isRefreshing = true }
                Resource.STATE_ERROR -> {
                    refreshLayout.isRefreshing = false
                    errorTitle.text = "Network Error"
                    errorBody.text = resource.message
                    errorLayout.visibility = View.VISIBLE
                }
                Resource.STATE_SUCCESS -> {
                    refreshLayout.isRefreshing = false
                    val data = resource.data
                    logger.log("data size ${data?.size}")
                    if (data?.isEmpty() == true) {
                        adapter.setFacility(facility)
                        errorTitle.text = "No Review"
                        errorBody.text = "This facility does not have any review"
                        errorLayout.visibility = View.VISIBLE

                        adapter.notifyDataSetChanged()
                    } else {
                        errorLayout.visibility = View.GONE
                        reviews.clear()
                       reviews.add(Review())
                        adapter.setFacility(facility)
                        data?.forEach { reviews.add(it) }

                        adapter.notifyDataSetChanged()
                    }
                }
            }
        })
    }

    private suspend fun submitReview(content: String) {
        viewModel.submitReview(facilityId = facility.sigUniqueId, content = content)
        viewModel.submitReviewLiveData().observe(this, androidx.lifecycle.Observer { resource ->
            when(resource.state) {
                Resource.STATE_LOADING -> { dialog.show() }
                Resource.STATE_SUCCESS -> {
                    dialog.cancel()
                    toast("Review Submitted")
                    lifecycleScope.launch {
                        viewModel.fetchReviews(facility.sigUniqueId)
                    }
                }
                Resource.STATE_ERROR -> {
                    dialog.cancel()
                    resource.message?.let { toast(it) }
                }
            }
        })
    }

    private fun showSubmitReviewDialog() {
        val dialog = AlertDialog.Builder(this, R.style.AlertDialogTheme)
        val contentView = LayoutInflater.from(this).inflate(R.layout.layout_add_review, null, false)
        dialog.setView(contentView)

        //This replaces both the 'val edittext' and the 'setText' lines
        binding.edtSubmitReview.setText(prevText)
        dialog.setNegativeButton("CANCEL", { d, _ -> d.dismiss() })
        dialog.setPositiveButton("SUBMIT", {d, _ ->
            val contentText = binding.edittext.text.toString().trim()
            if (contentText.isEmpty()) {
                toast("Add review text before you submit...")
               return@setPositiveButton
            }

            prevText = contentText
            d.dismiss()
            lifecycleScope.launch {
                submitReview(contentText)

            }
        })

        dialog.create().show()
    }

}