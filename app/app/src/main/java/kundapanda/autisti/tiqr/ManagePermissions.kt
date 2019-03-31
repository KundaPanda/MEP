package kundapanda.autisti.tiqr


import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS
import android.support.design.widget.Snackbar
import android.support.design.widget.Snackbar.LENGTH_LONG
import android.support.v4.app.ActivityCompat
import android.support.v4.content.ContextCompat
import android.support.v7.app.AlertDialog
import android.util.Log
import android.view.View
import android.widget.Toast


class ManagePermissions(val activity: Activity, private val permissionsList: List<String>, private val code: Int) {

    // Check permissions at runtime
    fun checkPermissions() {
        if (isPermissionsGranted() != PackageManager.PERMISSION_GRANTED) {
            requestPermissions()
        } else {
            Toast.makeText(activity, "Permissions already granted.", Toast.LENGTH_LONG).show()
        }
    }


    // Check permissions status
    private fun isPermissionsGranted(): Int {
        // PERMISSION_GRANTED : Constant Value: 0
        // PERMISSION_DENIED : Constant Value: -1
        var counter = 0
        for (permission in permissionsList) {
            counter += ContextCompat.checkSelfPermission(activity, permission)
        }
        return counter
    }


    // Find the first denied permission
    private fun deniedPermission(): String {
        for (permission in permissionsList) {
            if (ContextCompat.checkSelfPermission(activity, permission)
                == PackageManager.PERMISSION_DENIED
            ) return permission
        }
        return ""
    }


    private fun getPermissionLabel(permission: String, packageManager: PackageManager): CharSequence? {
        try {
            val permissionInfo = packageManager.getPermissionInfo(permission, 0)
            return permissionInfo.loadLabel(packageManager)
        } catch (e: PackageManager.NameNotFoundException) {
            e.printStackTrace()
        }
        return null
    }


    // Request the permissions at run time
    private fun requestPermissions() {
        val permission = deniedPermission()
        if (ActivityCompat.shouldShowRequestPermissionRationale(activity, permission)) {
            Log.i("PERMS", "Should show")
            ActivityCompat.requestPermissions(activity, permissionsList.toTypedArray(), code)

            Snackbar.make(
                activity.currentFocus!!,
                "This app needs permission to ${getPermissionLabel(
                    permission,
                    activity.packageManager
                )} in order to function correctly, please allow them in settings.",
                LENGTH_LONG
            ).addCallback(
                object : Snackbar.Callback() {
                    override fun onShown(sb: Snackbar?) {
                        super.onShown(sb)
                    }

                    override fun onDismissed(transientBottomBar: Snackbar?, event: Int) {
                        super.onDismissed(transientBottomBar, event)
                        val requestSnackBar = Snackbar.make(
                            activity.currentFocus!!,
                            "Open settings?",
                            LENGTH_LONG
                        )
                        requestSnackBar.setAction("Ok", object : View.OnClickListener {
                            override fun onClick(v: View?) {
                                val intent = Intent()
                                intent.action = ACTION_APPLICATION_DETAILS_SETTINGS
                                intent.data = Uri.fromParts("package", activity.packageName, null)
                                activity.startActivity(intent)
                            }
                        }).show()
                    }
                }).show()
        } else {
            ActivityCompat.requestPermissions(activity, permissionsList.toTypedArray(), code)
        }
    }


    // Process permissions result
    fun processPermissionsResult(
        grantResults: IntArray
    ): Boolean {
        var result = 0
        if (grantResults.isNotEmpty()) {
            for (item in grantResults) {
                result += item
            }
        }
        if (result == PackageManager.PERMISSION_GRANTED) return true
        return false
    }
}