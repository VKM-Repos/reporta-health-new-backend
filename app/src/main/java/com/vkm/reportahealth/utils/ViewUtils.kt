package com.vkm.reportahealth.utils

import android.graphics.Bitmap
import android.graphics.Canvas
import android.view.View
import android.app.Activity
import android.view.inputmethod.InputMethodManager


object ViewUtils {

    @JvmStatic
    fun fromView(view: View): Bitmap {
        view.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED)
        view.layout(0, 0, view.getMeasuredWidth(), view.getMeasuredHeight())
        view.buildDrawingCache()
        val bitmap = Bitmap.createBitmap(view.getMeasuredWidth(), view.getMeasuredHeight(), Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val bg = view.getBackground()
        if (bg != null)
            bg.draw(canvas)

        view.draw(canvas)
        return bitmap
    }
}