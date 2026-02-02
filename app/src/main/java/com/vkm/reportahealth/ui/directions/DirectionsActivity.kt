package com.vkm.reportahealth.ui.directions

import android.annotation.SuppressLint
import android.app.ProgressDialog
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.Toast
import androidx.core.content.ContextCompat
import com.akexorcist.googledirection.DirectionCallback
import com.akexorcist.googledirection.GoogleDirection
import com.akexorcist.googledirection.constant.TransportMode
import com.akexorcist.googledirection.model.Direction
import com.akexorcist.googledirection.model.Route
import com.akexorcist.googledirection.util.DirectionConverter
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.SupportMapFragment
import com.google.android.gms.maps.model.*
import com.vkm.reportahealth.R
import com.vkm.reportahealth.data.models.Facility
import com.vkm.reportahealth.ui.base.BaseActivity
import com.vkm.reportahealth.utils.LocationHelper
import com.vkm.reportahealth.utils.Logger
import com.vkm.reportahealth.utils.ViewUtils
//import kotlinx.android.synthetic.main.activity_direction.*
//import kotlinx.android.synthetic.main.layout_direction_time_distance.*
import org.koin.android.ext.android.inject
import org.parceler.Parcels
import com.vkm.reportahealth.databinding.ActivityDirectionBinding
import com.google.android.material.bottomnavigation.BottomNavigationView
import androidx.navigation.findNavController
import androidx.navigation.fragment.findNavController


class DirectionsActivity: BaseActivity(), OnMapReadyCallback, DirectionCallback {
    private lateinit var binding: ActivityDirectionBinding

    private var googleMap: GoogleMap? = null
    private var facility: Facility? = null
    private val logger = Logger.with("Direction")

    private val locationHelper: LocationHelper by inject()
    private val dialog by lazy { ProgressDialog(this).apply { setMessage("Processing...") } }
//    private val timeDistanceView by lazy { findViewById<View>(R.id.directionAndDistanceLayout) }

    @SuppressLint("WrongViewCast")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_direction)

        val map = supportFragmentManager.findFragmentById(R.id.mapFragmentDirectionActivity) as SupportMapFragment
        map.getMapAsync(this)

        facility = Parcels.unwrap(intent?.getParcelableExtra(Facility.TAG))
        setupUI()

        binding = ActivityDirectionBinding.inflate(layoutInflater)
        setContentView(binding.root)
            val navigation = findViewById<BottomNavigationView>(R.id.navigation)

    }

    override fun onMapReady(p0: GoogleMap?) {
        googleMap = p0
        try {
            googleMap?.isMyLocationEnabled = true
            googleMap?.setMapStyle(MapStyleOptions.loadRawResourceStyle(this, R.raw.style_json))
        }catch (e: SecurityException) {}
    }

    private fun setupUI() {
        binding.backButton.setOnClickListener {

//        backButton.setOnClickListener {
            finish()
        }

        val to = LatLng(facility?.fetchLatitude()!!, facility?.fetchLongitude()!!)
        val local = locationHelper.fetchPersistedLocation()

        val from = LatLng(local.latitude, local.longitude)
        executeRouteGetter(from = from, to = to)
        binding.navigation.root.setOnClickListener {

//        navigation.setOnClickListener {
            val gmmIntentUri = Uri.parse("google.navigation:q=${facility?.fetchLatitude()},${facility?.fetchLongitude()}")
            val mapIntent = Intent(Intent.ACTION_VIEW, gmmIntentUri)
            mapIntent.setPackage("com.google.android.apps.maps")
            if (mapIntent.resolveActivity(packageManager) != null) {
                startActivity(mapIntent)
            } else {
                toast("You don't have the Google Maps app installed on your phone")
            }

        }
    }

    private fun executeRouteGetter(from: LatLng?, to: LatLng?) {
        if (from != null && to != null) {
            dialog.show()
            GoogleDirection.withServerKey(getString(R.string.google_maps_key))
                    .from(from)
                    .to(to)
                    .transportMode(TransportMode.DRIVING)
                    .execute(this)
        }
    }

    override fun onDirectionSuccess(direction: Direction?, rawBody: String?) {

        dialog.cancel()
        rawBody?.let { logger.log("body " + rawBody) }
        if (direction != null && direction.isOK) {
            val route = direction.routeList[0]

            val to = markerView()
            val bmp = ViewUtils.fromView(to)
            val location = locationHelper.fetchPersistedLocation()
            val destination = LatLng(facility?.fetchLatitude()!!, facility?.fetchLongitude()!!)

            googleMap?.addMarker(MarkerOptions().position(destination))
            googleMap?.addMarker(MarkerOptions().icon(BitmapDescriptorFactory.fromBitmap(bmp))
                .position(LatLng(location.latitude, location.longitude)))


            val directionPositionList = route.legList[0].directionPoint
            googleMap?.addPolyline(
                DirectionConverter.createPolyline(
                    this,
                    directionPositionList,
                    5,
                    ContextCompat.getColor(this, R.color.colorPrimary)
                )
            )
            setCameraWithCoordinationBounds(route)
            binding.navigation.root.visibility = View.VISIBLE

            val legs = route.legList
            if (legs.size > 0) {
                val first = legs[0]
                binding.navigation.totalDistanceTextView.text = first.distance.text
                binding.navigation.totalTimeTextView.text = first.duration.text

//                totalDistanceTextView.text = first.distance.text
//                totalTimeTextView.text = first.duration.text
            }
        }else {

            direction?.errorMessage?.let {
                Toast.makeText(this, it, Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun setCameraWithCoordinationBounds(route: Route) {
        val southwest = route.bound.southwestCoordination.coordination
        val northeast = route.bound.northeastCoordination.coordination
        val bounds = LatLngBounds(southwest, northeast)

        googleMap?.animateCamera(CameraUpdateFactory.newLatLngBounds(bounds, 100))
    }


    private fun markerView() = LayoutInflater.from(this).inflate(R.layout.layout_marker, null, false)
    override fun onDirectionFailure(t: Throwable?) {
        dialog.cancel()
        logger.logErr("$t")
    }
}