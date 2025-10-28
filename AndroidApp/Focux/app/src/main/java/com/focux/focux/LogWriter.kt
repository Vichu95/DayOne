package com.focux.focux

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object LogWriter {
    private const val FILE_NAME = "usage_log.txt"
    private val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US)

    fun append(context: Context, line: String) {
        val f = File(context.filesDir, FILE_NAME)
        f.appendText("${sdf.format(Date())} - $line\n")
    }

    fun read(context: Context): String {
        val f = File(context.filesDir, FILE_NAME)
        return if (f.exists()) f.readText() else ""
    }

    fun clear(context: Context) {
        val f = File(context.filesDir, FILE_NAME)
        if (f.exists()) f.writeText("")
    }
}
