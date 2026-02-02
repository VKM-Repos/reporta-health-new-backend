package com.vkm.reportahealth.ui.login

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.vkm.reportahealth.R
import com.vkm.reportahealth.ui.home.HomeActivity
import com.vkm.reportahealth.data.models.Auth

fun Auth.Companion.login(email: String, password: String, function: (Boolean, String) -> Unit) {}

class LoginActivity : AppCompatActivity() {

    private lateinit var emailInput: EditText
    private lateinit var passwordInput: EditText
    private lateinit var loginButton: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        emailInput = findViewById(R.id.emailInput)
        passwordInput = findViewById(R.id.passwordInput)
        loginButton = findViewById(R.id.loginButton)
        progressBar = findViewById(R.id.progressBar)

        loginButton.setOnClickListener {
            val email = emailInput.text.toString()
            val password = passwordInput.text.toString()

            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Enter email and password", Toast.LENGTH_SHORT).show()
            } else {
                loginUser(email, password)
            }
        }
    }

    private fun loginUser(email: String, password: String) {
        progressBar.visibility = View.VISIBLE
        loginButton.isEnabled = false

        // Call Auth.kt login function here
        Auth.login(email, password) { success: Boolean, message: String ->
            // Everything that depends on 'success' or 'message' MUST stay inside here
            if (success) {
                println("Login successful!")
                val intent = Intent(this@LoginActivity, HomeActivity::class.java)
                startActivity(intent)
                finish()
            } else {
                println("Error: $message")
                Toast.makeText(this@LoginActivity, message, Toast.LENGTH_SHORT).show()
            }
        }}}




