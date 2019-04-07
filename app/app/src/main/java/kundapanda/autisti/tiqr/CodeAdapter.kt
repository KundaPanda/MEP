package kundapanda.autisti.tiqr

import android.app.Activity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.ImageButton
import android.widget.TextView
import java.util.*


class CodeAdapter(private val activity: Activity, private val users: ArrayList<Code>) : ArrayAdapter<Code>(activity, 0, users) {

    override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
        var view = convertView
        if (view == null) {
            view = LayoutInflater.from(context).inflate(R.layout.item_scan_history, parent, false)
        }
        val code = getItem(position)

        val deleteButton = view!!.findViewById<ImageButton>(R.id.delete_button)
        deleteButton.setOnClickListener {
            users.removeAt(position)
            notifyDataSetChanged()
        }

        val codeCode = view!!.findViewById(R.id.history_item_code) as TextView
        val codeResponse = view.findViewById(R.id.history_item_response) as TextView
        val codeTime = view.findViewById(R.id.history_item_time) as TextView

        codeCode.text = code!!.code
        codeResponse.text = code.response
        codeTime.text = code.time

        return view
    }


    override fun getCount(): Int {
        return users.size
    }

    fun getCode(pos: Int): Any {
        return users[pos]
    }

    fun getCodeCode(pos: Int): String {
        return users[pos].code
    }
}
