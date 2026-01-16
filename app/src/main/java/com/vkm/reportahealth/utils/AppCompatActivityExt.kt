package com.vkm.reportahealth.utils

import androidx.annotation.IdRes
import androidx.appcompat.app.ActionBar
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentManager
import androidx.fragment.app.FragmentTransaction

/**
 * Author: Omolara Adejuwon
 * Date: 24/02/2019.
 */
/**
 * The `fragment` is added to the container view with id `frameId`. The operation is
 * performed by the `fragmentManager`.
 * Note that this clears the back stage if flag is provided
 */
fun AppCompatActivity.replaceFragmentInActivity(fragment: Fragment, frameId: Int, tag: String? = null) {
    supportFragmentManager.transact {
        replace(frameId, fragment, tag)
    }
}

fun AppCompatActivity.popAllFragmentsInActivity() {
    supportFragmentManager.popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE)
}

fun AppCompatActivity.pushFragmentIntoActivity(fragment: Fragment, frameId: Int, tag: String? = null) {
    supportFragmentManager.transact {
        //        setCustomAnimations(R.anim.enter_from_right, R.anim.exit_to_left, R.anim.enter_from_left, R.anim.exit_to_right)
        replace(frameId, fragment, tag)
        addToBackStack(tag)
    }
}


/**
 * The `fragment` is added to the container view with tag. The operation is
 * performed by the `fragmentManager`.
 */
fun AppCompatActivity.addFragmentToActivity(fragment: Fragment, tag: String) {
    supportFragmentManager.transact {
        add(fragment, tag)
    }
}

fun AppCompatActivity.setupActionBar(@IdRes toolbarId: Int, action: ActionBar.() -> Unit) {
    setSupportActionBar(findViewById(toolbarId))
    supportActionBar?.run {
        action()
    }
}

/**
 * Runs a FragmentTransaction, then calls commit().
 */
private inline fun FragmentManager.transact(action: FragmentTransaction.() -> Unit) {
    beginTransaction().apply {
        action()
    }.commit()
}

/**
 * used when back button is pressed and you want to go to the previous fragment
 */
fun AppCompatActivity.pop(callback: () -> Unit) {
    val count = supportFragmentManager.backStackEntryCount
    if (count >= 1) {
        supportFragmentManager.popBackStack()
    } else {
        callback()
    }
}