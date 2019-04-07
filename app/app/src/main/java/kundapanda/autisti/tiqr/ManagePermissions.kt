package kundapanda.autisti.tiqr


import android.app.Activity
import android.content.pm.PackageManager
import android.support.v4.app.ActivityCompat
import android.support.v4.content.ContextCompat
import android.widget.Toast


class ManagePermissions(val activity: Activity, private val permissionsList: List<String>, private val code: Int) {

    // Check permissions at runtime
    fun checkPermissions(): Boolean {
        if (isPermissionsGranted() != PackageManager.PERMISSION_GRANTED) {
            requestPermissions()
        } else {
            Toast.makeText(activity, "Permissions already granted.", Toast.LENGTH_SHORT).show()
            return true
        }
        return false
    }


    // Check permissions status
    private fun isPermissionsGranted(): Int {
        // PERMISSION_GRANTED : 0
        // PERMISSION_DENIED : -1
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

    // Find permission description
    fun getPermissionLabel(permission: String, packageManager: PackageManager): CharSequence? {
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
            ActivityCompat.requestPermissions(activity, permissionsList.toTypedArray(), code)
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