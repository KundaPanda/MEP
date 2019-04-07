package kundapanda.autisti.tiqr

import android.util.Base64
import org.json.JSONObject
import java.io.*
import java.net.HttpURLConnection
import java.net.URL
import javax.net.ssl.HttpsURLConnection

class RequestHandler {

    private var username: String? = null
    private var password: String? = null
    private var protocol: String = "https://"

    /**
     * Sends http or https post requests to the provided url
     * returns json as a string or '1' if invalid or '2' if connection error
     */
    fun sendPostRequest(
        requestURL: String,
        ticket: String?
    ): String {
        val url: URL
        // stringBuilder object to store the message retrieved from the server
        val stringBuilder: java.lang.StringBuilder
        try {
            // initializing Url
            url = URL(protocol + requestURL)
            if (protocol == "http://") {
                val conn = url.openConnection() as HttpURLConnection
                // set Basic auth
                processBasicAuth(conn)
                // set desired connection properties
                conn.readTimeout = 2500
                conn.connectTimeout = 2500
                conn.requestMethod = "POST"
                conn.doInput = true
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")

                val outputStream = conn.outputStream
                // if code is provided, send it as a json object
                if (ticket != null) {
                    val jsonTicket = JSONObject()
                    jsonTicket.accumulate("code", ticket)
                    val writer = BufferedWriter(OutputStreamWriter(outputStream, "UTF-8"))
                    writer.write(jsonTicket.toString())
                    writer.flush()
                    writer.close()
                }
                outputStream.close()
                val responseCode = conn.responseCode
                // evaluate response
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    val bufferedReader = BufferedReader(InputStreamReader(conn.inputStream))
                    stringBuilder = StringBuilder()
                    var response: String?
                    // read response body
                    response = bufferedReader.readLine()
                    while (response != null) {
                        stringBuilder.append(response)
                        response = bufferedReader.readLine()
                    }
                    return stringBuilder.toString().replace("\n", "").replace("\r", "")
                } else if (responseCode == HttpURLConnection.HTTP_NOT_MODIFIED) {
                    return "1"
                }

            } else {
                val conn = url.openConnection() as HttpsURLConnection
                // set Basic auth with ssl
                processBasicAuthSSL(conn)
                // set desired connection properties
                conn.readTimeout = 2500
                conn.connectTimeout = 2500
                conn.requestMethod = "POST"
                conn.doInput = true
                conn.doOutput = true

                val os = conn.outputStream
                // if a code is provided, send it as a json object
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
                // evaluate the response
                if (responseCode == HttpsURLConnection.HTTP_OK) {
                    val bufferedReader = BufferedReader(InputStreamReader(conn.inputStream))
                    stringBuilder = StringBuilder()
                    var response: String?
                    // read response body
                    response = bufferedReader.readLine()
                    while (response != null) {
                        response = bufferedReader.readLine()
                        stringBuilder.append(response)
                    }
                    // remove all newlines
                    return stringBuilder.toString().replace("\n", "").replace("\r", "")
                } else if (responseCode == HttpsURLConnection.HTTP_NOT_MODIFIED) {
                    return "1"
                }

            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return "2"
    }

    /**
     * checks if server is available and has a specific port open
     */
    fun checkServerAvailable(serverAddress: String, serverPort: Int): Boolean {
        try {
            val url = URL("$protocol$serverAddress:$serverPort/api/client/check_login")
            if (protocol == "http://") {
                val connection = url.openConnection() as HttpURLConnection
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                // return either 200 or 401
                return connection.responseCode in arrayOf(
                    HttpURLConnection.HTTP_UNAUTHORIZED,
                    HttpURLConnection.HTTP_OK
                )
            } else {
                val connection = url.openConnection() as HttpsURLConnection
                connection.connectTimeout = 2500
                connection.readTimeout = 2500
                connection.requestMethod = "POST"
                // return either 200 or 401
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

    /**
     * checks if connection was successful with a provided login
     */
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

    /**
     * adds basic auth arguments to headers of a connection
     */
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

    /**
     * adds basic auth arguments to headers of a connection with ssl
     */
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
        } else {
            this.protocol = "https://"
        }
    }
}