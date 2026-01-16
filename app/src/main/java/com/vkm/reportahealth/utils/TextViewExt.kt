package com.vkm.reportahealth.utils

import android.text.SpannableString
import android.text.style.UnderlineSpan
import android.view.View

/**
 * Author: Omolara Adejuwon
 * Date: 2019-06-30.
 */
fun String.underline():SpannableString {
    val content = SpannableString(this)
    content.setSpan(UnderlineSpan(), 0, this.length, 0)
    return  content
}

fun View.show() {
    visibility = View.VISIBLE
}

fun View.hide() {
    visibility = View.GONE
}