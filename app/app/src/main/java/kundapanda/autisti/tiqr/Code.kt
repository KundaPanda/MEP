package kundapanda.autisti.tiqr

import java.text.SimpleDateFormat
import java.util.*

class Code {
    var code = ""
    var response = ""
    var time = ""

    constructor()

    constructor(code: String, response: String, time: String) {
        this.code = code
        this.response = response
        this.time = time
    }

    override fun equals(other: Any?): Boolean {
        return super.equals(other)
    }

    override fun hashCode(): Int {
        return super.hashCode()
    }


    override fun toString(): String {
        return ("Code [code=" + code + ", response=" + response + ", time="
                + time + "]")
    }
}