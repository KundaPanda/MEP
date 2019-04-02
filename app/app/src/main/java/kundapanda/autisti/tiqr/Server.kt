package kundapanda.autisti.tiqr

import android.Manifest.permission.*
import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.annotation.TargetApi
import android.content.Context
import android.content.Intent
import android.os.AsyncTask
import android.os.Build
import android.os.Bundle
import android.support.design.widget.Snackbar
import android.support.design.widget.Snackbar.LENGTH_INDEFINITE
import android.support.v7.app.AppCompatActivity
import android.support.v7.app.AppCompatDelegate
import android.util.Log
import android.util.Patterns
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.view.inputmethod.EditorInfo
import android.webkit.URLUtil
import android.widget.TextView
import android.widget.Toast
import kotlinx.android.synthetic.main.activity_server.*
import java.net.MalformedURLException
import java.net.UnknownHostException


/**
 * A login screen that offers login via email/password.
 */
class Server : AppCompatActivity() {
    /**
     * Keep track of the login task to ensure we can cancel it if requested.
     */
    private val defaultServerPortStr = "5432"
    private var serverPingTask: ServerPingTask? = null
    private val permissionsRequestCode = 200
    private lateinit var managePermissions: ManagePermissions
    private val permissionsList = listOf(
        CAMERA,
        WRITE_EXTERNAL_STORAGE,
        INTERNET
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        val currentTheme = ThemeEnum.getTheme(this)
        if (currentTheme == ThemeEnum.Light) {
            setTheme(R.style.AppTheme_Light)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        } else {
            setTheme(R.style.AppTheme_Dark)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        }

        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_server)
//        delegate.setLocalNightMode(AppCompatDelegate.MODE_NIGHT_YES)

        managePermissions = ManagePermissions(this, permissionsList, permissionsRequestCode)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            managePermissions.checkPermissions()
        }

        val token = getSharedPreferences("server", Context.MODE_PRIVATE)
        var protocol = getSharedPreferences("server", Context.MODE_PRIVATE).getString("protocol", "")

        if (protocol == "") {
            getSharedPreferences("server", Context.MODE_PRIVATE).edit().putString("protocol", "http://").apply()
            protocol = "http://"
        }

        protocol_mode_switch.isChecked = (protocol == "http://")

        server_id.setOnEditorActionListener(TextView.OnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_DONE || id == EditorInfo.IME_NULL) {
                attemptConfirm()
                return@OnEditorActionListener true
            }
            false
        })

        protocol_mode_switch.setOnClickListener(fun(view: View) {
            val editor = getSharedPreferences("server", Context.MODE_PRIVATE).edit()
            if (protocol_mode_switch.isChecked) {
                editor.putString("protocol", "https://")
                protocol_mode_switch.text = this.getString(R.string.protocol_mode_https)
            } else {
                editor.putString("protocol", "http://")
                protocol_mode_switch.text = this.getString(R.string.protocol_mode_http)
            }
            editor.apply()
        })

        val serverStr = token.getString("address", "")!!
        val serverPortStr = token.getString("port", "")!!
        val autoConnect = token.getBoolean("autoConnect", false)
        val serverProtocol = token.getString("protocol", "https://")

        protocol_mode_switch.isChecked = (serverProtocol == "https://")

        if (serverStr != "" && serverPortStr != "") {
            server_id.text.insert(server_id.selectionStart, serverStr)
            server_port_id.text.insert(server_port_id.selectionStart, serverPortStr)
            if (autoConnect) {
                attemptConfirm(serverStr, serverPortStr)
            }
        }

        sever_confirm_button.setOnClickListener { attemptConfirm() }
    }


    /**
     * Attempts to sign in or register the account specified by the login form.
     * If there are form errors (invalid email, missing fields, etc.), the
     * errors are presented and no actual login attempt is made.
     */
    private fun attemptConfirm(
        serverStr: String = server_id.text.toString(),
        serverPortStr: String = server_port_id.text.toString()
    ) {
        if (serverPingTask != null) {
            return
        }

        var modifiedServerStr: String = serverStr
        var modifiedPortStr: String = serverPortStr

        if (modifiedServerStr.take(7) == "http://") {
            modifiedServerStr = modifiedServerStr.replace("https://", "")
        } else if (modifiedServerStr.take(8) == "https://") {
            modifiedServerStr = modifiedServerStr.replace("http://", "")
        }
        modifiedServerStr = modifiedServerStr.replace("[\\s]", "")
        modifiedPortStr = modifiedPortStr.replace("[\\s]", "")
        if (modifiedPortStr.isEmpty()) {
            modifiedPortStr = defaultServerPortStr
        }

        // Reset errors.
        server_id.error = null
        server_port_id.error = null

        val focusView: View?

        if (!isServerPortValid(modifiedPortStr)) {
            server_port_id.error = getString(R.string.error_invalid_server_port)
            focusView = server_port_id
            focusView?.requestFocus()
        } else {
            // Check for a valid password, if the user entered one.
            if (!isServerValid(modifiedServerStr)) {
                server_id.error = getString(R.string.error_invalid_server)
                focusView = server_id

                // There was an error; don't attempt login and focus the first
                // form field with an error.
                focusView?.requestFocus()
            } else {
                // Show a progress spinner, and kick off a background task to
                // perform the user login attempt.
                showProgress(true)
                // remove all whitespaces
                serverPingTask = ServerPingTask(modifiedServerStr, modifiedPortStr)
                serverPingTask!!.execute(null as Void?)
            }
        }

    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.navbar_menu, menu)
        return super.onCreateOptionsMenu(menu)
    }

    override fun onOptionsItemSelected(item: MenuItem?): Boolean {
        val id = item!!.itemId
        when (id) {
            (R.id.mode_toggle) -> ThemeEnum.switchTheme(this, this)
        }
        return super.onOptionsItemSelected(item)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>,
        grantResults: IntArray
    ) {
        when (requestCode) {
            permissionsRequestCode -> {
                val isPermissionsGranted = managePermissions
                    .processPermissionsResult(grantResults)

                if (isPermissionsGranted) {
                    // Do the task now
                    Toast.makeText(this, "Permissions granted.", Toast.LENGTH_LONG).show()
                } else {
                    Snackbar.make(
                        this.currentFocus!!,
                        "This application cannot function properly without requested permissions.",
                        LENGTH_INDEFINITE
                    ).show()
                }
                return
            }
        }
    }

    private fun isServerValid(serverStr: String): Boolean {
        try {
            if ((URLUtil.isValidUrl(serverStr) || (Patterns.WEB_URL.matcher(serverStr).matches()) || (serverStr.split(".").size == 4))) {
                return true
            }
        } catch (e: MalformedURLException) {
        }
        return false
    }

    private fun isServerPortValid(serverPortStr: String): Boolean {
        if (serverPortStr.toInt() in 1..65535) {
            return true
        }
        return false
    }

    /**
     * Shows the progress UI and hides the login form.
     */
    @TargetApi(Build.VERSION_CODES.HONEYCOMB_MR2)
    private fun showProgress(show: Boolean) {
        // On Honeycomb MR2 we have the ViewPropertyAnimator APIs, which allow
        // for very easy animations. If available, use these APIs to fade-in
        // the progress spinner.

        val shortAnimTime = resources.getInteger(android.R.integer.config_shortAnimTime).toLong()

        server_form.visibility = if (show) View.GONE else View.VISIBLE
        server_form.animate()
            .setDuration(shortAnimTime)
            .alpha((if (show) 0 else 1).toFloat())
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    server_form.visibility = if (show) View.GONE else View.VISIBLE
                }
            })

        server_check_progress.visibility = if (show) View.VISIBLE else View.GONE
        server_check_progress.animate()
            .setDuration(shortAnimTime)
            .alpha((if (show) 1 else 0).toFloat())
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    server_check_progress.visibility = if (show) View.VISIBLE else View.GONE
                }
            })

    }

    /**
     * Represents an asynchronous server checking task used to check
     * if the server responds to pinging.
     */
    private inner class ServerPingTask internal constructor(
        private val serverCheckAddress: String,
        private var serverCheckPort: String
    ) :
        AsyncTask<Void, Void, Boolean>() {

        override fun doInBackground(vararg params: Void): Boolean? {

            try {
                val protocol = getSharedPreferences("server", Context.MODE_PRIVATE).getString("protocol", "https://")!!
                val requestHandler = RequestHandler()
                requestHandler.setTransmissionProtocol(protocol)
                val response = requestHandler.checkServerAvailable(serverCheckAddress, serverCheckPort.toInt())
                if (response) {
                    Log.d("CONNECT", "connection successful")
                    return true
                }
            } catch (e: UnknownHostException) {
                e.printStackTrace()
            } catch (e: Exception) {
                e.printStackTrace()
            }
            Log.d("CONNECT", "connection unsuccessful")
            return false
        }

        override fun onPostExecute(success: Boolean?) {
            serverPingTask = null
            showProgress(false)

            if (success!!) {
                val token = getSharedPreferences("server", Context.MODE_PRIVATE)
                val editor = token.edit()
                if ((token.getString("address", "") != serverCheckAddress)
                    || (token.getString("port", "") != serverCheckPort)
                ) {
                    editor.putString("address", serverCheckAddress)
                    editor.putString("port", serverCheckPort)
                }
                editor.putBoolean("autoConnect", autoconnect_checkbox.isChecked)
                editor.apply()

                val intent = Intent(this@Server, Login::class.java)
                startActivity(intent)

                finish()
            } else {
                server_id.error = getString(R.string.error_unreachable_server)
                server_id.requestFocus()
            }
        }

        override fun onCancelled() {
            serverPingTask = null
            showProgress(false)
        }
    }

}
