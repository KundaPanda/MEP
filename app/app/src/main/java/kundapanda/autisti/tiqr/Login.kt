package kundapanda.autisti.tiqr

import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.annotation.TargetApi
import android.content.Context
import android.content.Intent
import android.os.AsyncTask
import android.os.Build
import android.os.Bundle
import android.support.v7.app.AppCompatActivity
import android.support.v7.app.AppCompatDelegate
import android.text.TextUtils
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.TextView
import kotlinx.android.synthetic.main.activity_login.*
import kotlinx.android.synthetic.main.activity_toolbar.*

/**
 * A login screen
 */
class Login : AppCompatActivity() {
    /**
     * Keep track of the login task to ensure we can cancel it if requested.
     */
    private var mAuthTask: UserLoginTask? = null

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
        setContentView(R.layout.activity_login)
        setSupportActionBar(toolbar)

        // check permissions and request if needed
        password_id.setOnEditorActionListener(TextView.OnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_DONE || id == EditorInfo.IME_NULL) {
                attemptLogin()
                return@OnEditorActionListener true
            }
            false
        })

        // load all shared preferences
        val token = getSharedPreferences("login", Context.MODE_PRIVATE)
        val uName = token.getString("username", "")!!
        val uPass = token.getString("password", "")!!
        val autoLogin = token.getBoolean("autoLogin", false)

        // if saved values are not empty, fill textViews
        if (uName != "" && uPass != "") {
            login_id.text.insert(login_id.selectionStart, uName)
            password_id.text.insert(password_id.selectionStart, uPass)
            // if autoLogin is enabled, login
            if (autoLogin) {
                attemptLogin(uName, uPass)
            }
        }

        // add onclick listener for login button
        sign_in_button.setOnClickListener { attemptLogin() }

        // add onclick listener to return to server edit screen
        login_to_server_button.setOnClickListener {
            getSharedPreferences("server", Context.MODE_PRIVATE).edit().putBoolean("autoConnect", false).apply()
            val intent = Intent(this, Server::class.java)
            startActivity(intent)
            finish()
        }
    }


    /**
     * Attempts to login with provided credentials
     */
    private fun attemptLogin(
        loginStr: String = login_id.text.toString(),
        passwordStr: String = password_id.text.toString()
    ) {
        if (mAuthTask != null) {
            return
        }

        // Reset errors.
        login_id.error = null
        password_id.error = null

        var cancel = false
        var focusView: View? = null

        // Check for a valid password
        if (TextUtils.isEmpty(passwordStr) || !isPasswordValid(passwordStr)) {
            password_id.error = getString(R.string.error_invalid_password)
            focusView = password_id
            cancel = true
        }

        // Check for a valid login
        if (TextUtils.isEmpty(loginStr) || !isLoginValid(loginStr)) {
            login_id.error = getString(R.string.error_field_required)
            focusView = login_id
            cancel = true
        }

        if (cancel) {
            // There was an error; don't attempt login and focus the first
            // form field with an error.
            focusView?.requestFocus()
        } else {
            // Show a progress spinner, and kick off a background task to
            // perform the user login attempt.
            showProgress(true)
            mAuthTask = UserLoginTask(loginStr, passwordStr)
            mAuthTask!!.execute(null as Void?)
        }
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

    private fun isPasswordValid(password: String): Boolean {
        // simple check, can be changed easily here
        return password.length > 4
    }

    private fun isLoginValid(login: String): Boolean {
        // simple check, can be changed easily here
        return login.length > 4
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

        login_form.visibility = if (show) View.GONE else View.VISIBLE
        login_form.animate()
            .setDuration(shortAnimTime)
            .alpha((if (show) 0 else 1).toFloat())
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    login_form.visibility = if (show) View.GONE else View.VISIBLE
                }
            })

        login_progress.visibility = if (show) View.VISIBLE else View.GONE
        login_progress.animate()
            .setDuration(shortAnimTime)
            .alpha((if (show) 1 else 0).toFloat())
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    login_progress.visibility = if (show) View.VISIBLE else View.GONE
                }
            })

    }

    /**
     * Represents an asynchronous login task used to authenticate the user.
     */
    private inner class UserLoginTask internal constructor(private val mLogin: String, private val mPassword: String) :
        // leaks won't occur as the activity won't close until this task is finished, could be done on main thread, but it would lock ui progress bar
        AsyncTask<Void, Void, Boolean>() {

        override fun doInBackground(vararg params: Void): Boolean? {
            try {
                // load server details
                val token = getSharedPreferences("server", Context.MODE_PRIVATE)
                val address = token.getString("address", "")!!
                val port = token.getString("port", "")!!
                val protocol = token.getString("protocol", "")!!
                if (address != "" && port != "") {
                    // attempt connection to server with provided credentials
                    val requestHandler = RequestHandler()
                    requestHandler.setTransmissionProtocol(protocol)
                    requestHandler.setBasicAuth(mLogin, mPassword)
                    val response = requestHandler.checkServerLoginValid(address, port.toInt())
                    if (!response) {
                        return false
                    }
                }
            } catch (e: InterruptedException) {
                return false
            }
            return true
        }

        override fun onPostExecute(success: Boolean?) {
            mAuthTask = null
            showProgress(false)

            if (success!!) {
                // if log-in successful, save into shared preferences and go to scanner
                val token = getSharedPreferences("login", Context.MODE_PRIVATE)
                val editor = token.edit()
                if (token.getString("username", "") != mLogin || token.getString("password", "") != mPassword) {
                    editor.putString("username", mLogin)
                    editor.putString("password", mPassword)
                }
                editor.putBoolean("autoLogin", autologin_checkbox.isChecked)
                editor.apply()
                val intent = Intent(this@Login, Scanner::class.java)
                startActivity(intent)
                finish()
            } else {
                // show error message
                password_id.error = getString(R.string.error_incorrect_password)
                password_id.requestFocus()
            }
        }

        override fun onCancelled() {
            mAuthTask = null
            showProgress(false)
        }
    }

}
