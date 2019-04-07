package kundapanda.autisti.tiqr

import android.Manifest.permission.*
import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.annotation.TargetApi
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.AsyncTask
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.support.design.widget.Snackbar
import android.support.v7.app.AppCompatActivity
import android.support.v7.app.AppCompatDelegate
import android.util.Patterns
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.webkit.URLUtil
import android.widget.TextView
import android.widget.Toast
import kotlinx.android.synthetic.main.activity_server.*
import kotlinx.android.synthetic.main.activity_toolbar.*
import java.net.MalformedURLException
import java.net.UnknownHostException


/**
 * A server address input screen
 */
class Server : AppCompatActivity() {
    private val defaultServerPortStr = "5000"
    private var serverPingTask: ServerPingTask? = null
    private val permissionsRequestCode = 200
    private lateinit var managePermissions: ManagePermissions
    private val permissionsList = listOf(
        CAMERA,
        WRITE_EXTERNAL_STORAGE,
        INTERNET
    )
    private var offlineMode = false
    private var permissionsGranted = false

    override fun onCreate(savedInstanceState: Bundle?) {
        // set theme from shared prefs
        val currentTheme = ThemeEnum.getTheme(this)
        if (currentTheme == ThemeEnum.Light) {
            setTheme(R.style.AppTheme_Light)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        } else {
            setTheme(R.style.AppTheme_Dark)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        }

        // inflate layout and add toolbar
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_server)
        setSupportActionBar(toolbar)

        // check permissions and request if needed
        managePermissions = ManagePermissions(this, permissionsList, permissionsRequestCode)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (managePermissions.checkPermissions()) {
                permissionsGranted = true
            }
        }

        // load protocol and offlineMode from shared preferences, set its default value to https
        val token = getSharedPreferences("server", Context.MODE_PRIVATE)
        var protocol = getSharedPreferences("server", Context.MODE_PRIVATE).getString("protocol", "")!!
        offlineMode = getSharedPreferences("server", Context.MODE_PRIVATE).getBoolean("offlineMode", false)

        // save default protocol as https
        if (protocol == "") {
            getSharedPreferences("server", Context.MODE_PRIVATE).edit().putString("protocol", "https://").apply()
            protocol = "https://"
        }
        // set switch according to offlineMode
        offline_mode_switch.isChecked = offlineMode

        // set switch and text according to protocol
        protocol_mode_switch.isChecked = (protocol == "https://")
        protocol_mode_switch.text = protocol.replace("://", "")


        // starts confirm upon pressing enter in TextView
        server_id.setOnEditorActionListener(TextView.OnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_DONE || id == EditorInfo.IME_NULL) {
                attemptConfirm()
                return@OnEditorActionListener true
            }
            false
        })

        // change 'confirm' button behavior based on offlineMode toggle
        offline_mode_switch.setOnClickListener {
            if (offline_mode_switch.isChecked) {
                offlineMode = true
                server_confirm_button.setOnClickListener { offlineConfirm() }
            } else {
                offlineMode = false
                server_confirm_button.setOnClickListener { attemptConfirm() }
            }
        }

        // must be set in order to work without changing offline mode
        if (offlineMode) {
            server_confirm_button.setOnClickListener { offlineConfirm() }
        } else {
            server_confirm_button.setOnClickListener { attemptConfirm() }
        }

        protocol_mode_switch.setOnClickListener(protocolTextChange)

        // load saved values from shared preferences
        val serverStr = token.getString("address", "")!!
        val serverPortStr = token.getString("port", "")!!
        val autoConnect = token.getBoolean("autoConnect", false)

        if (offlineMode && autoConnect) {
            offlineConfirm(serverStr, serverPortStr)
        }

        // if saved values are not empty, fill textViews
        if (serverStr != "" && serverPortStr != "") {
            server_id.text.insert(server_id.selectionStart, serverStr)
            server_port_id.text.insert(server_port_id.selectionStart, serverPortStr)
            // if autoConnect is checked, connect with saved values
            if (autoConnect) {
                attemptConfirm(serverStr, serverPortStr)
            }
        }
    }

    /**
     * Sets shared preferences and protocol button text to values according to protocol button state
     */
    private val protocolTextChange = View.OnClickListener {
        val editor = getSharedPreferences("server", Context.MODE_PRIVATE).edit()
        if (protocol_mode_switch.isChecked) {
            editor.putString("protocol", "https://")
            protocol_mode_switch.text = this.getString(R.string.protocol_mode_https)
        } else {
            editor.putString("protocol", "http://")
            protocol_mode_switch.text = this.getString(R.string.protocol_mode_http)
        }
        editor.apply()
    }


    /**
     * Attempts to connect to the server with given values
     */
    private fun attemptConfirm(
        serverStr: String = server_id.text.toString(),
        serverPortStr: String = server_port_id.text.toString()
    ) {
        if (!permissionsGranted) {
            showBlockingToast()
            return
        }

        if (serverPingTask != null) {
            return
        }

        // reset errors
        server_id.error = null
        server_port_id.error = null

        // replace all spaces and http(s):// in the entered address
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

        val focusView: View?
        // if port is not valid, stop checking and set error message
        if (!isServerPortValid(modifiedPortStr)) {
            server_port_id.error = getString(R.string.error_invalid_server_port)
            focusView = server_port_id
            focusView?.requestFocus()
        } else {
            // check if server is valid
            if (!isServerValid(modifiedServerStr)) {
                server_id.error = getString(R.string.error_invalid_server)
                focusView = server_id
                focusView?.requestFocus()
            } else {
                // Show a progress spinner and try to connect to the server
                showProgress(true)
                serverPingTask = ServerPingTask(modifiedServerStr, modifiedPortStr)
                serverPingTask!!.execute(null as Void?)
            }
        }

    }

    /**
     * shows toast message about permissions
     */
    private fun showBlockingToast() {
        Toast.makeText(this, "You cannot use this app until requested permissions will have been granted. \n Please grant these permissions in settings and restart the app.", Toast.LENGTH_LONG).show()
    }

    /**
     * Attempts to connect to the server with given values
     */
    private fun offlineConfirm(
        serverStr: String = server_id.text.toString(),
        serverPortStr: String = server_port_id.text.toString()
    ) {
        if (!permissionsGranted) {
            showBlockingToast()
            return
        }
        // reset errors
        server_id.error = null
        server_port_id.error = null

        // replace all spaces and http(s):// in the entered address
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

        // save all entered values, autoConnect checkbox and protocol
        val token = getSharedPreferences("server", Context.MODE_PRIVATE)
        val editor = token.edit()
        if ((token.getString("address", "") != modifiedServerStr)
            || (token.getString("port", "") != modifiedPortStr)
        ) {
            editor.putString("address", modifiedServerStr)
            editor.putString("port", modifiedPortStr)
        }
        editor.putBoolean("autoConnect", autoconnect_checkbox.isChecked)
        editor.putBoolean("offlineMode", offline_mode_switch.isChecked)
        editor.apply()
        // proceed directly to scanner
        val intent = Intent(this@Server, Scanner::class.java)
        startActivity(intent)
        finish()

    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        // Inflate the action bar
        menuInflater.inflate(R.menu.navbar_menu, menu)
        return true
    }


    override fun onOptionsItemSelected(item: MenuItem?): Boolean {
        // add onclick listener for theme switch button
        val id = item!!.itemId
        when (id) {
            (R.id.mode_toggle) -> ThemeEnum.switchTheme(this, this)
        }
        return super.onOptionsItemSelected(item)
    }

    /**
     * shows response after requesting permissions
     */
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
                    permissionsGranted = true
                    Toast.makeText(this, "Permissions granted.", Toast.LENGTH_LONG).show()
                } else {
                    permissionsGranted = false
                    val viewGroup = (this.findViewById(android.R.id.content) as ViewGroup).getChildAt(0) as ViewGroup
                    Snackbar.make(
                        viewGroup,
                        "This app needs permission to ${managePermissions.getPermissionLabel(
                            permissions[0],
                            packageManager
                        )} in order to function correctly, please allow them in settings.",
                        Snackbar.LENGTH_LONG
                    ).addCallback(
                        object : Snackbar.Callback() {
                            override fun onDismissed(transientBottomBar: Snackbar?, event: Int) {
                                super.onDismissed(transientBottomBar, event)
                                val requestSnackBar = Snackbar.make(
                                    viewGroup,
                                    "Open settings?",
                                    Snackbar.LENGTH_LONG
                                )
                                requestSnackBar.setAction("Ok") {
                                    val intent = Intent()
                                    intent.action = Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                                    intent.data = Uri.fromParts("package", packageName, null)
                                    startActivity(intent)

                                }.show()
                            }
                        }).show()
                }
                return
            }
        }
    }

    /**
     * checks if server is valid by checking if it is an ipv4 or a valid url
     */
    private fun isServerValid(serverStr: String): Boolean {
        try {
            if ((URLUtil.isValidUrl(serverStr) || (Patterns.WEB_URL.matcher(serverStr).matches()) || (serverStr.split(".").size == 4))) {
                return true
            }
        } catch (e: MalformedURLException) {
        }
        return false
    }

    /**
     * checks if port is in possible range
     */
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
    // leaks won't occur as the activity won't close until this task is finished, could be done on main thread, but it would lock ui progress bar
        AsyncTask<Void, Void, Boolean>() {

        override fun doInBackground(vararg params: Void): Boolean? {
            // try to connect in background
            try {
                val protocol = getSharedPreferences("server", Context.MODE_PRIVATE).getString("protocol", "https://")!!
                val requestHandler = RequestHandler()
                requestHandler.setTransmissionProtocol(protocol)
                val response = requestHandler.checkServerAvailable(serverCheckAddress, serverCheckPort.toInt())
                if (response) {
                    return true
                }
            } catch (e: UnknownHostException) {
                e.printStackTrace()
            } catch (e: Exception) {
                e.printStackTrace()
            }
            return false
        }

        override fun onPostExecute(success: Boolean?) {
            serverPingTask = null
            showProgress(false)

            if (success!!) {
                // save all entered values, autoConnect checkbox and protocol
                val token = getSharedPreferences("server", Context.MODE_PRIVATE)
                val editor = token.edit()
                if ((token.getString("address", "") != serverCheckAddress)
                    || (token.getString("port", "") != serverCheckPort)
                ) {
                    editor.putString("address", serverCheckAddress)
                    editor.putString("port", serverCheckPort)
                }
                editor.putBoolean("offlineMode", offline_mode_switch.isChecked)
                editor.putBoolean("autoConnect", autoconnect_checkbox.isChecked)
                editor.apply()
                // proceed to login
                val intent = Intent(this@Server, Login::class.java)
                startActivity(intent)
                finish()
            } else {
                // set errors if not successful
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
