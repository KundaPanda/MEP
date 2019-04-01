package kundapanda.autisti.tiqr

import android.util.Base64
import android.util.JsonWriter
import android.util.Log
import org.json.JSONObject
import java.io.*
import java.net.HttpURLConnection
import java.net.HttpURLConnection.HTTP_OK
import java.net.URL
import java.net.URLEncoder
import java.nio.Buffer
import java.util.*
import javax.net.ssl.HttpsURLConnection

/**
 * Created by ZERO on 16/08/2016.
 */
class RequestHandler {

    private var username: String? = null
    private var password: String? = null
    private var protocol: String = "https://"

    //Method to send httpPostRequest
    //This method is taking two arguments
    //First argument is the URL of the script to which we will send the request
    //Other is an HashMap with name value pairs containing the data to be send with the request
    fun sendPostRequest(
        requestURL: String,
        ticket: String?
    ): String {
        val url: URL

        //StringBuilder object to store the message retrieved from the server
        var sb = StringBuilder()
        try {
            //Initializing Url
            Log.d("URL", "Connecting to: $requestURL")
            url = URL(protocol + requestURL)

            if (protocol == "http://") {
                val conn = url.openConnection() as HttpURLConnection
                //set Basic auth
                processBasicAuth(conn)

                //Configuring connection properties
                conn.readTimeout = 2500
                conn.connectTimeout = 2500
                conn.requestMethod = "POST"
                conn.doInput = true
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");

                //Creating an output stream
                val os = conn.outputStream

                //Writing parameters to the request
                //We are using a method getPostDataString which is defined below
                if (ticket != null) {
                    val jsonTicket = JSONObject()
                    jsonTicket.accumulate("code", ticket)
                    val writer = BufferedWriter(OutputStreamWriter(os, "UTF-8"))
                    writer.write(jsonTicket.toString())
                    writer.flush()
                    writer.close()
                }

                os.close()
                val responseCode = conn.responseCode

                if (responseCode == HttpURLConnection.HTTP_OK) {

                    val br = BufferedReader(InputStreamReader(conn.inputStream))
                    sb = StringBuilder()
                    var response: String?
                    //Reading server response
                    response = br.readLine()
                    while (response != null) {
                        sb.append(response)
                        response = br.readLine()
                    }
                    return sb.toString().replace("\n", "").replace("\r", "");
                } else if (responseCode == HttpURLConnection.HTTP_NOT_MODIFIED) {
                    return "1"
                }

            } else {
                val conn = url.openConnection() as HttpsURLConnection
                //set Basic auth
                processBasicAuthSSL(conn)

                //Configuring connection properties
                conn.readTimeout = 2500
                conn.connectTimeout = 2500
                conn.requestMethod = "POST"
                conn.doInput = true
                conn.doOutput = true

                //Creating an output stream
                val os = conn.outputStream

                //Writing parameters to the request
                //We are using a method getPostDataString which is defined below
                if (ticket != null) {
                    val jsonTicket = JSONObject()
                    jsonTicket.accumulate("code", ticket)
                    val writer = BufferedWriter(OutputStreamWriter(os, "UTF-8"))
                    writer.write(jsonTicket.toString())
                    writer.flush()
                    writer.close()
                }

                os.close()
                val responseCode = conn.responseCode

                if (responseCode == HttpsURLConnection.HTTP_OK) {

                    val br = BufferedReader(InputStreamReader(conn.inputStream))
                    sb = StringBuilder()
                    var response: String?
                    //Reading server response
                    response = br.readLine()
                    while (response != null) {
                        response = br.readLine()
                        sb.append(response)
                    }
                    return sb.toString().replace("\n", "").replace("\r", "");
                } else if (responseCode == HttpsURLConnection.HTTP_NOT_MODIFIED) {
                    return "1"
                }

            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return "2"
    }

    fun checkServerAvailable(serverAddress: String, serverPort: Int): Boolean {
        try {
            val url = URL("$protocol$serverAddress:$serverPort/api/client/check_login")
            if (protocol == "http://") {
                val connection = url.openConnection() as HttpURLConnection
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                return connection.responseCode in arrayOf(
                    HttpURLConnection.HTTP_UNAUTHORIZED,
                    HttpURLConnection.HTTP_OK
                )
            } else {
                val connection = url.openConnection() as HttpsURLConnection
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                return connection.responseCode in arrayOf(
                    HttpsURLConnection.HTTP_UNAUTHORIZED,
                    HttpsURLConnection.HTTP_OK
                )
            }
        } catch (e: IOException) {
            e.printStackTrace()
        }
        return false
    }

    fun checkServerLoginValid(serverAddress: String, serverPort: Int): Boolean {
        try {
            val url = URL("$protocol$serverAddress:$serverPort/api/client/check_login")
            if (protocol == "http://") {
                val connection = url.openConnection() as HttpURLConnection
                processBasicAuth(connection)
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                connection.doInput = true
                val responseCode = connection.responseCode
                connection.disconnect()
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    return true
                }
            } else {
                val connection = url.openConnection() as HttpsURLConnection
                processBasicAuthSSL(connection)
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                connection.doInput = true
                val responseCode = connection.responseCode
                connection.disconnect()
                if (responseCode == HttpsURLConnection.HTTP_OK) {
                    return true
                }
            }
        } catch (e: IOException) {
        }
        return false
    }

    private fun processBasicAuth(conn: HttpURLConnection) {
        if (username != null && password != null) {
            try {
                val userCredentials = "$username:$password"
                val data = userCredentials.toByteArray(charset = Charsets.UTF_8)
                val base64 = Base64.encodeToString(data, Base64.DEFAULT)
                conn.addRequestProperty("Authorization", "Basic $base64")
            } catch (e: UnsupportedEncodingException) {
                e.printStackTrace()
            }

        }
    }

    private fun processBasicAuthSSL(conn: HttpsURLConnection) {
        if (username != null && password != null) {
            try {
                val userCredentials = "$username:$password"
                val data = userCredentials.toByteArray(charset = Charsets.UTF_8)
                val base64 = Base64.encodeToString(data, Base64.DEFAULT)
                conn.addRequestProperty("Authorization", "Basic $base64")
            } catch (e: UnsupportedEncodingException) {
                e.printStackTrace()
            }

        }
    }

    fun setBasicAuth(username: String, password: String) {
        this.username = username
        this.password = password
    }

    fun setTransmissionProtocol(protocol: String) {
        if (protocol in arrayOf("https://", "http://")) {
            this.protocol = protocol
        }
    }
}