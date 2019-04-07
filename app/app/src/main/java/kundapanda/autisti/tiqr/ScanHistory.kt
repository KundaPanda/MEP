package kundapanda.autisti.tiqr

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.support.v7.app.AppCompatActivity
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
        setContentView(R.layout.activity_scan_history)
        super.onCreate(savedInstanceState)
        listView = findViewById(R.id.history_list_view)

        scanner_button.setOnClickListener {
            val intent = Intent(this, Scanner::class.java)
            startActivity(intent)
            finish()
        }

        val historyToken = getSharedPreferences("history", Context.MODE_PRIVATE)
        val codesJSON = historyToken.getString("codesJson", JSONArray().toString())
        val gson = Gson()
        val type = object : TypeToken<List<Code>>() {}.type
        codesArrayList = gson.fromJson(codesJSON, type)
        val adapter = CodeAdapter(this, codesArrayList)
        listView.adapter = adapter
    }

    override fun onDestroy() {
        super.onDestroy()
        save(this)
    }

    fun addCode(code: Code, context: Context) {
        val historyToken = context.getSharedPreferences("history", Context.MODE_PRIVATE)
        val codesJSON = historyToken.getString("codesJson", JSONArray().toString())
        val gson = Gson()
        val type = object : TypeToken<List<Code>>() {}.type
        codesArrayList = gson.fromJson(codesJSON, type)
        codesArrayList.add(code)
        save(context)
    }

    fun clearAll() {
        adapter.clear()
        codesArrayList = ArrayList<Code>()
    }

    fun deleteCode(position: Int) {
        codesArrayList.remove(codesArrayList[position])
        adapter.notifyDataSetChanged()
    }

    fun save(context: Context) {
        val codesJson = Gson().toJson(codesArrayList)
        val historyToken = context.getSharedPreferences("history", Context.MODE_PRIVATE)
        historyToken.edit().putString("codesJson", codesJson.toString()).apply()
    }

}