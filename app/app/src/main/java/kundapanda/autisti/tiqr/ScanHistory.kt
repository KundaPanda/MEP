package kundapanda.autisti.tiqr

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.support.v7.app.AppCompatActivity
import android.support.v7.app.AppCompatDelegate
import android.widget.ListView
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.android.synthetic.main.activity_scan_history.*
import org.json.JSONArray


class ScanHistory : AppCompatActivity() {

    private lateinit var listView: ListView
    private lateinit var adapter: CodeAdapter
    private var codesArrayList: ArrayList<Code> = ArrayList<Code>()

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
        // inflate layout, set view
        setContentView(R.layout.activity_scan_history)
        super.onCreate(savedInstanceState)
        listView = findViewById(R.id.history_list_view)
        // add onclick listener for 'bacK' button
        scanner_button.setOnClickListener {
            val intent = Intent(this, Scanner::class.java)
            startActivity(intent)
            finish()
        }
        // load shared preferences
        val historyToken = getSharedPreferences("history", Context.MODE_PRIVATE)
        val codesJSON = historyToken.getString("codesJson", JSONArray().toString())
        // convert json string to ArrayList
        val gson = Gson()
        val type = object : TypeToken<List<Code>>() {}.type
        codesArrayList = gson.fromJson(codesJSON, type)
        // start view adapter
        val adapter = CodeAdapter(this, codesArrayList)
        listView.adapter = adapter
    }

    override fun onDestroy() {
        // save into shared preferences on exit
        super.onDestroy()
        save(this)
    }

    /**
     * adds a code to array
     */
    fun addCode(code: Code, context: Context) {
        val historyToken = context.getSharedPreferences("history", Context.MODE_PRIVATE)
        val codesJSON = historyToken.getString("codesJson", JSONArray().toString())
        val gson = Gson()
        val type = object : TypeToken<List<Code>>() {}.type
        codesArrayList = gson.fromJson(codesJSON, type)
        codesArrayList.add(code)
        save(context)
    }

    /**
     * deletes all codes
     */
    fun clearAll() {
        adapter.clear()
        codesArrayList = ArrayList<Code>()
    }

    /**
     * deletes a single code
     */
    fun deleteCode(position: Int) {
        codesArrayList.remove(codesArrayList[position])
        adapter.notifyDataSetChanged()
    }

    /**
     * saves current ArrayList to json shared preferences
     */
    fun save(context: Context) {
        val codesJson = Gson().toJson(codesArrayList)
        val historyToken = context.getSharedPreferences("history", Context.MODE_PRIVATE)
        historyToken.edit().putString("codesJson", codesJson.toString()).apply()
    }

}