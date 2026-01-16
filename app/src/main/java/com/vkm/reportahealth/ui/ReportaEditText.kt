package com.vkm.reportahealth.ui

import android.content.Context
import android.graphics.Canvas
import android.util.AttributeSet
import android.view.Gravity
import android.view.View
import android.widget.EditText
import android.widget.FrameLayout
import androidx.core.content.ContextCompat
import com.vkm.reportahealth.R
import com.vkm.reportahealth.utils.onTextChange

class ReportaEditText @JvmOverloads constructor(context: Context, attributeSet: AttributeSet? = null,
                                                style: Int = 0) : FrameLayout(context, attributeSet, style) {

    companion object {
        const val GRAVITY_TOP = 1
        const val GRAVTTY_CENTER = 2
    }


    private val editText by lazy { findViewById<EditText>(R.id.valueEditText) }
    private val errorView by lazy { findViewById<View>(R.id.errorIndicatorView) }

    init {
        View.inflate(context, R.layout.layout_reporta_edittext, this)
        editText.onTextChange { newText ->
            if (newText.isNotEmpty()) clearError()
        }
    }

    fun getEdiText() = editText
    fun getText() = editText.text.toString().trim()

    fun setHint(hint: String) {
        editText.hint = hint
    }

    fun indicateError(message: String) {
        editText.hint = message
        editText.setHintTextColor(ContextCompat.getColor(context, R.color.red))
        errorView.visibility = View.VISIBLE
        requestFocus()
    }

    fun setGravity(gravity: Int) {
        val newGravity = when(gravity) {
            GRAVITY_TOP -> Gravity.TOP
            GRAVTTY_CENTER -> Gravity.CENTER_VERTICAL
            else -> Gravity.CENTER_VERTICAL
        }

        if (gravity == GRAVITY_TOP) editText.setPadding(0, 5, 0, 0)
        editText.gravity = newGravity
    }

    fun setText(s: String) {
        editText.setText(s)
    }

    fun clearError() {
        editText.setHintTextColor(ContextCompat.getColor(context, R.color.textColorSecondary))
        errorView.visibility = View.GONE
    }

    override fun onDraw(canvas: Canvas) { // Remove the '?' if your parent class allows
        super.onDraw(canvas)
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec)
    }
}