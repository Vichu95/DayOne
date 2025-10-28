package com.example.phoneusagetracker


import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

class ForegroundService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = NotificationCompat.Builder(this, "track_channel")
            .setContentTitle("Phone Usage Tracker")
            .setContentText("Tracking in background")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .build()

        startForeground(1, notification)
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
