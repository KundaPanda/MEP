package kundapanda.autisti.tiqr

import android.Manifest
import android.Manifest.permission.CAMERA
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.support.design.widget.NavigationView
import android.support.design.widget.Snackbar
import android.support.design.widget.Snackbar.LENGTH_INDEFINITE
import android.support.v4.content.ContextCompat
import android.support.v4.view.GravityCompat
import android.support.v7.app.AlertDialog
import android.support.v7.app.AppCompatActivity
import android.support.v7.app.AppCompatDelegate
import android.util.SparseArray
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import com.google.android.gms.vision.CameraSource
import com.google.android.gms.vision.CameraSource.CAMERA_FACING_BACK
import com.google.android.gms.vision.Detector
import com.google.android.gms.vision.barcode.Barcode
import com.google.android.gms.vision.barcode.BarcodeDetector
import kotlinx.android.synthetic.main.activity_scanner.*
import kotlinx.android.synthetic.main.activity_toolbar.*
import kotlinx.android.synthetic.main.app_bar_scanner.*
import kotlinx.android.synthetic.main.content_scanner.*
import kotlinx.android.synthetic.main.nav_header_scanner.view.*
import org.json.JSONException
import org.json.JSONObject


class Scanner : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {

    private val permissionsRequestCode = 200
    private lateinit var managePermissions: ManagePermissions
    private val permissionsList = listOf(
        CAMERA,
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
        Manifest.permission.INTERNET
    )
    private lateinit var cameraSource: CameraSource
    private lateinit var detector: BarcodeDetector
    private var offlineMode = false

    override fun onCreate(savedInstanceState: Bundle?) {
        // select theme based od shared prefs
        val currentTheme = ThemeEnum.getTheme(this)
        if (currentTheme == ThemeEnum.Light) {
            setTheme(R.style.AppTheme_Light)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        } else {
            setTheme(R.style.AppTheme_Dark)
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        }
        // inflate views and toolbar
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scanner)
        setSupportActionBar(toolbar)

        // add floating button and navbar listeners
        nav_view.setNavigationItemSelectedListener(this)
        fab.setOnClickListener {
            val handler = Handler(Looper.getMainLooper())
            handler.post { setupBarcodeDetector() }
        }
        // start detector and camera
        setupBarcodeDetector()
        // load all preferences
        val loginToken = getSharedPreferences("login", Context.MODE_PRIVATE)
        val serverToken = getSharedPreferences("server", Context.MODE_PRIVATE)
        val userName = loginToken.getString("username", "")!!
        val serverAddress = serverToken.getString("address", "")!!
        val serverPort = serverToken.getString("port", "")!!
        val serverUrl = "$serverAddress:$serverPort"
        offlineMode = serverToken.getBoolean("offlineMode", false)

        if (!offlineMode) {
            if (userName != "") {
                nav_view.getHeaderView(0).nav_user_login.text = userName
            }

            if (serverAddress != "" && serverPort != "") {
                nav_view.getHeaderView(0).nav_server_address.text = serverUrl
            }
        } else {
            nav_view.getHeaderView(0).nav_user_login.text = resources.getText(R.string.offline_mode)
            nav_view.getHeaderView(0).nav_server_address.text = resources.getText(R.string.offline_mode)
        }

    }

    override fun onPause() {
        super.onPause()
        camera_view.stop()
    }

    override fun onResume() {
        super.onResume()
        camera_view.start(cameraSource, camera_view_overlay)
    }


    private fun setupBarcodeDetector() {
        // build a new detector
        detector = BarcodeDetector.Builder(applicationContext)
            .setBarcodeFormats(Barcode.QR_CODE)
            .build()

        // check if build successful
        if (!detector.isOperational) {
            val snackBar = Snackbar.make(
                this.currentFocus!!,
                "This application cannot function properly without requested permissions.",
                LENGTH_INDEFINITE
            )
            snackBar.setAction("Dismiss") { snackBar.dismiss() }.show()
            return
        }
        // build camera source and add detector as handler
        cameraSource = CameraSource.Builder(this, detector)
            .setFacing(CAMERA_FACING_BACK)
            .setAutoFocusEnabled(true)
            .setRequestedFps(30.toFloat())
            .build()

        // start camera preview after setup
        if (ContextCompat.checkSelfPermission(this, CAMERA) == PackageManager.PERMISSION_GRANTED) {
            camera_view.start(cameraSource, camera_view_overlay)
        } else {
            Snackbar.make(this.currentFocus!!, "Camera permission not granted", Snackbar.LENGTH_LONG).show()
        }

        // set detector responses
        detector.setProcessor(object : Detector.Processor<Barcode> {
            override fun release() {
            }

            override fun receiveDetections(detections: Detector.Detections<Barcode>) {
                // when code is scanned:
                val barCodes: SparseArray<Barcode> = detections.detectedItems
                if (barCodes.size() > 0) {
                    // create a new handler on main (ui) thread for displaying responses, as this runs in the background on another thread
                    val handler = Handler(Looper.getMainLooper())
                    val scannedCode = barCodes.valueAt(0).rawValue
                    // stop detections and camera preview
                    handler.post {
                        camera_view.release()
                        detector.release()
                    }

                    if (offlineMode) {
                        handler.post {
                            val alertDialog = AlertDialog.Builder(this@Scanner, R.style.AlertDialogOffline).create()
                            alertDialog.setTitle("Scanned code:")
                            alertDialog.setMessage(scannedCode)
                            alertDialog.setButton(
                                AlertDialog.BUTTON_NEUTRAL, "OK"
                            ) { dialog, _ -> dialog.dismiss() }
                            alertDialog.show()
                        }
                    } else {
                        val loginToken = getSharedPreferences("login", Context.MODE_PRIVATE)
                        val serverToken = getSharedPreferences("server", Context.MODE_PRIVATE)
                        val userName = loginToken.getString("username", "")!!
                        val userPassword = loginToken.getString("password", "")!!
                        val serverAddress = serverToken.getString("address", "")!!
                        val serverPort = serverToken.getString("port", "")!!
                        val serverProtocol = serverToken.getString("protocol", "")!!
                        val serverUrl = "$serverAddress:$serverPort"
                        // send post request to server
                        val request = RequestHandler()
                        request.setTransmissionProtocol(serverProtocol)
                        request.setBasicAuth(userName, userPassword)
                        val response = request.sendPostRequest("$serverUrl/api/client", scannedCode)
                        var responseMessage: String? = null
                        var responseStatus = 0
                        when (response) {
                            "1" -> {
                                // invalid code
                                responseMessage = "$scannedCode is not a valid code."
                                responseStatus = 1
                            }
                            "2" -> {
                                // error in connection
                                responseMessage = "Error communicating with the server. Scanned code was: $scannedCode."
                                responseStatus = 2
                            }
                            else -> {
                                // valid code
                                try {
                                    val jsonMessage = JSONObject(response)
                                    if (jsonMessage.getInt("used") != 0) {
                                        responseMessage =
                                            "Code $scannedCode has already been used ${jsonMessage.getInt("used")} times. Latest check was at: ${jsonMessage.getString(
                                                "time"
                                            )}."
                                        responseStatus = 1
                                    } else {
                                        responseMessage = "Code $scannedCode is valid."
                                    }
                                } catch (e: JSONException) {
                                    e.printStackTrace()
                                }
                            }
                        }

                        if (responseMessage != null) {
                            // set style based on response
                            val responseStyle = when (responseStatus) {
                                0 -> (R.style.AlertDialogSuccess)
                                1 -> (R.style.AlertDialogFail)
                                2 -> (R.style.AlertDialogError)
                                else -> R.style.AlertDialogError
                            }
                            // create new dialog with response
                            handler.post {
                                val alertDialog = AlertDialog.Builder(this@Scanner, responseStyle).create()
                                alertDialog.setTitle("Server response:")
                                alertDialog.setMessage(responseMessage)
                                alertDialog.setButton(
                                    AlertDialog.BUTTON_NEUTRAL, "OK"
                                ) { dialog, _ -> dialog.dismiss() }
                                alertDialog.show()
                            }

                        } else {
                            // create error snackBar
                            val snackBar =
                                Snackbar.make(
                                    scanner_view,
                                    "Unable to parse JSON response for code $scannedCode.",
                                    LENGTH_INDEFINITE
                                )
                            snackBar.setAction("Dismiss") { snackBar.dismiss() }.show()
                        }
                    }
                }
            }
        })
    }

    override fun onBackPressed() {
        // either close navbar or exit
        if (scanner_drawer_layout.isDrawerOpen(GravityCompat.START)) {
            scanner_drawer_layout.closeDrawer(GravityCompat.START)
        } else {
            super.onBackPressed()
            camera_view.stop()
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        // Inflate the action bar
        menuInflater.inflate(R.menu.navbar_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        // switch theme
        when (item.itemId) {
            (R.id.mode_toggle) -> ThemeEnum.switchTheme(this, this)
        }
        return super.onOptionsItemSelected(item)
    }

    /**
     * response creator based on permission request result
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
                    Toast.makeText(this, "Permissions granted.", Toast.LENGTH_LONG).show()
                } else {
                    Snackbar.make(
                        this.currentFocus!!, "This application cannot function properly without requested permissions.",
                        Snackbar.LENGTH_INDEFINITE
                    ).show()
                }
                return
            }
        }
    }


    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        // Handle navigation view item clicks here.
        when (item.itemId) {
            R.id.nav_change_login -> {
                // disable autoLogin and go to login screen
                val token = getSharedPreferences("login", Context.MODE_PRIVATE)
                val editor = token.edit()
                editor.putBoolean("autoLogin", false)
                editor.apply()
                intent = Intent(this, Login::class.java)
                startActivity(intent)
                camera_view.stop()
                finish()
            }
            R.id.nav_request_permissions -> {
                // re-check permissions
                managePermissions = ManagePermissions(this, permissionsList, permissionsRequestCode)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    managePermissions.checkPermissions()
                }
            }
            R.id.nav_change_server -> {
                // disable autoConnect and go to server preferences screen
                val token = getSharedPreferences("server", Context.MODE_PRIVATE)
                val editor = token.edit()
                editor.putBoolean("autoConnect", false)
                editor.apply()
                intent = Intent(this, Server::class.java)
                startActivity(intent)
                camera_view.stop()
                finish()
            }
        }


        scanner_drawer_layout.closeDrawer(GravityCompat.START)
        return true
    }
}
