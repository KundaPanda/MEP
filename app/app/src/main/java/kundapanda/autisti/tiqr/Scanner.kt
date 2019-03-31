package kundapanda.autisti.tiqr

import android.Manifest
import android.Manifest.permission.CAMERA
import android.app.ProgressDialog.show
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.support.design.widget.NavigationView
import android.support.design.widget.Snackbar
import android.support.design.widget.Snackbar.LENGTH_INDEFINITE
import android.support.v4.content.ContextCompat
import android.support.v4.view.GravityCompat
import android.support.v4.view.accessibility.AccessibilityEventCompat.setAction
import android.support.v7.app.ActionBarDrawerToggle
import android.support.v7.app.AppCompatActivity
import android.util.SparseArray
import android.view.Menu
import android.view.MenuItem
import android.widget.TextView
import android.widget.Toast
import com.google.android.gms.vision.CameraSource
import com.google.android.gms.vision.CameraSource.CAMERA_FACING_BACK
import com.google.android.gms.vision.Detector
import com.google.android.gms.vision.barcode.Barcode
import com.google.android.gms.vision.barcode.BarcodeDetector
import kotlinx.android.synthetic.main.activity_scanner.*
import kotlinx.android.synthetic.main.app_bar_scanner.*
import kotlinx.android.synthetic.main.content_scanner.*
import kotlinx.android.synthetic.main.nav_header_scanner.*
import org.json.JSONException
import org.json.JSONObject
import kotlin.math.log

class Scanner : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {


    private val permissionsRequestCode = 200
    private lateinit var managePermissions: ManagePermissions
    private val permissionsList = listOf(
        CAMERA,
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
        Manifest.permission.INTERNET
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scanner)
        setSupportActionBar(toolbar)

        val toggle = ActionBarDrawerToggle(
            this, scanner_drawer_layout, toolbar, R.string.navigation_drawer_open, R.string.navigation_drawer_close
        )
        scanner_drawer_layout.addDrawerListener(toggle)
        toggle.syncState()

        nav_view.setNavigationItemSelectedListener(this)
        fab.setOnClickListener { view ->
            Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
                .setAction("Action", null).show()
        }

        val detector = BarcodeDetector.Builder(applicationContext)
            .setBarcodeFormats(Barcode.QR_CODE)
            .build()

        if (!detector!!.isOperational) {
            scan_results.text = R.string.scanner_non_functional.toString()
            return
        }


        val cameraSource = CameraSource.Builder(this, detector)
            .setFacing(CAMERA_FACING_BACK)
            .setAutoFocusEnabled(true)
            .setRequestedFps(30.toFloat())
            .build()

        detector.setProcessor(object : Detector.Processor<Barcode> {
            override fun release() {
                TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
            }

            override fun receiveDetections(detections: Detector.Detections<Barcode>) {
                val loginToken = getSharedPreferences("login", Context.MODE_PRIVATE)
                val serverToken = getSharedPreferences("server", Context.MODE_PRIVATE)
                val userName = loginToken.getString("username", "")!!
                val userPassword = loginToken.getString("password", "")!!
                val serverAddress = serverToken.getString("address", "")!!
                val serverPort = serverToken.getString("port", "")!!
                val serverUrl = "$serverAddress:$serverPort"

                val barCodes: SparseArray<Barcode> = detections.detectedItems
                if (barCodes.size() > 0) {
                    val scannedCode = barCodes.valueAt(0).rawValue
                    Snackbar.make(scanner_view, "Received code: $scannedCode", Snackbar.LENGTH_LONG)
                        .show()
                    val request = RequestHandler()
                    request.setBasicAuth(userName, userPassword)
                    val response = request.sendPostRequest(serverAddress, scannedCode)
                    var responseMessage: String? = null
                    var responseColor: Int? = null
                    if (response == "1") {
                        responseMessage = "$scannedCode is not a valid code."
                        responseColor = Color.MAGENTA
                    } else if (response == "2") {
                        responseMessage = "Error connecting to the server."
                        responseColor = Color.MAGENTA
                    } else {
                        try {
                            val jsonMessage = JSONObject(response)
                            if (jsonMessage.getInt("used") != 0) {
                                responseMessage =
                                    "Code $scannedCode has already been used ${jsonMessage.getInt("used")} times. Latest check was at: ${jsonMessage.getString(
                                        "time"
                                    )}."
                                responseColor = Color.RED
                            } else {
                                responseMessage = "Code $scannedCode is valid."
                                responseColor = Color.GREEN
                            }
                        } catch (e: JSONException) {
                            e.printStackTrace()
                        }
                    }

                    if (responseMessage != null) {
                        val snackBar = Snackbar.make(scanner_view, responseMessage, LENGTH_INDEFINITE)
                            .setActionTextColor(Color.MAGENTA)
                        val snackBarView = snackBar.view.findViewById(R.id.snackbar_text) as TextView
                        snackBarView.setTextColor(responseColor!!)
                        snackBar.setAction("Dismiss", { scanner_view -> snackBar.dismiss() })
                            .show()
                    } else {
                        val snackBar = Snackbar.make(scanner_view, "Unable to parse JSON response.", LENGTH_INDEFINITE)
                        snackBar.setAction("Dismiss", { scanner_view -> snackBar.dismiss() }).show()
                    }
                    TODO("not yet implemented")
                }
            }
        })

        if (ContextCompat.checkSelfPermission(this, CAMERA) == PackageManager.PERMISSION_GRANTED) {
            camera_view.start(cameraSource, camera_view_overlay)
        } else {
            Snackbar.make(this.currentFocus!!, "Camera permission not granted", Snackbar.LENGTH_LONG).show()
        }

    }

    override fun onBackPressed() {
        if (scanner_drawer_layout.isDrawerOpen(GravityCompat.START)) {
            scanner_drawer_layout.closeDrawer(GravityCompat.START)
        } else {
            super.onBackPressed()
            camera_view.release()
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        // Inflate the menu; this adds items to the action bar if it is present.
        menuInflater.inflate(R.menu.scanner, menu)
        val loginToken = getSharedPreferences("login", Context.MODE_PRIVATE)
        val serverToken = getSharedPreferences("server", Context.MODE_PRIVATE)
        val userName = loginToken.getString("username", "")!!
        val serverAddress = serverToken.getString("address", "")!!
        val serverPort = serverToken.getString("port", "")!!
        val serverUrl = "$serverAddress:$serverPort"

        if (userName != "") {
            nav_user_login.text = userName
        }

        if (serverAddress != "" && serverPort != "") {
            nav_server_address.text = serverUrl
        }

        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        when (item.itemId) {
            R.id.action_settings -> return true
            else -> return super.onOptionsItemSelected(item)
        }
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
                val token = getSharedPreferences("login", Context.MODE_PRIVATE)
                val editor = token.edit()
                editor.putString("username", "")
                editor.putString("password", "")
                editor.apply()
                intent = Intent(this, Login::class.java)
                startActivity(intent)
                camera_view.release()
                finish()
            }
            R.id.nav_request_permissions -> {
                managePermissions = ManagePermissions(this, permissionsList, permissionsRequestCode)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    managePermissions.checkPermissions()
                }
            }
            R.id.nav_change_server -> {
                val token = getSharedPreferences("server", Context.MODE_PRIVATE)
                val editor = token.edit()
                editor.putString("server", "")
                editor.apply()
                intent = Intent(this, Server::class.java)
                startActivity(intent)
                camera_view.release()
                finish()
            }
            R.id.nav_manage -> {

            }
            R.id.nav_share -> {

            }
            R.id.nav_send -> {

            }
        }


        scanner_drawer_layout.closeDrawer(GravityCompat.START)
        return true
    }
}
