package kundapanda.autisti.tiqr

import android.util.Base64
import android.util.JsonWriter
import android.util.Log
import org.json.JSONObject
import java.io.*
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.*
import javax.net.ssl.HttpsURLConnection

/**
 * Created by ZERO on 16/08/2016.
 */
class RequestHandler {

    private var username: String? = null
    private var password: String? = null

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
            url = URL(requestURL + "/api/client")

            //Creating an httmlurl connection
            val conn = url.openConnection() as HttpURLConnection
            //set Basic auth
            processBasicAuth(conn)

            //Configuring connection properties
            conn.readTimeout = 4500
            conn.connectTimeout = 4500
            conn.requestMethod = "POST"
            conn.doInput = true
            conn.doOutput = true

            //Creating an output stream
            val os = conn.outputStream

            //Writing parameters to the request
            //We are using a method getPostDataString which is defined below
            val writer = JsonWriter(
                OutputStreamWriter(os, "UTF-8")
            )
            if (ticket != null) {
                writer.beginObject()
                writer.name("ticket").value(ticket)
                writer.endObject()
            }

            writer.flush()
            writer.close()
            os.close()
            val responseCode = conn.responseCode

            if (responseCode == HttpsURLConnection.HTTP_OK) {

                val br = BufferedReader(InputStreamReader(conn.inputStream))
                sb = StringBuilder()
                val response: String
                //Reading server response
                response = br.readLine()
                while (response != null) {
                    sb.append(response)
                }
                return sb.toString()
            } else if (responseCode == HttpsURLConnection.HTTP_NOT_MODIFIED) {
                return "1"
            }

        } catch (e: Exception) {
            e.printStackTrace()
        }
        return "2"
    }

    private fun processBasicAuth(conn: HttpURLConnection) {
        if (username != null && password != null) {
            try {
                val userPassword = "$username:$password"
                val data = userPassword.toByteArray(charset("UTF-8"))
                val base64 = Base64.encodeToString(data, Base64.DEFAULT)
                conn.setRequestProperty("Authorization", "Basic $base64")
            } catch (e: UnsupportedEncodingException) {
                e.printStackTrace()
            }

        }
    }

    fun sendGetRequest(requestURL: String): String {
        val sb = StringBuilder()
        try {
            val url = URL(requestURL)
            val con = url.openConnection() as HttpURLConnection
            //set Basic auth
            processBasicAuth(con)
            val bufferedReader = BufferedReader(InputStreamReader(con.inputStream))

            val s = bufferedReader.readLine()
            while (s != null) {
                sb.append(s + "\n")
            }
        } catch (e: Exception) {
        }

        return sb.toString()
    }

    fun sendGetRequestParam(requestURL: String, id: String): String {
        val sb = StringBuilder()
        try {
            val url = URL(requestURL + id)
            val con = url.openConnection() as HttpURLConnection
            val bufferedReader = BufferedReader(InputStreamReader(con.inputStream))

            val s = bufferedReader.readLine()
            while (s != null) {
                sb.append(s + "\n")
            }
        } catch (e: Exception) {
        }

        return sb.toString()
    }

    @Throws(UnsupportedEncodingException::class)
    private fun getPostDataString(params: HashMap<String?, String?>): String {
        val result = StringBuilder()
        var first = true
        for ((key, value) in params) {
            if (key != null && value != null) {
                if (first)
                    first = false
                else
                    result.append("&")

                result.append(URLEncoder.encode(key, "UTF-8"))
                result.append("=")
                result.append(URLEncoder.encode(value, "UTF-8"))
            }
        }

        return result.toString()
    }

    fun setBasicAuth(username: String, password: String) {
        this.username = username
        this.password = password
    }
}