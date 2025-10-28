package com.example.phoneusagetracker

import android.app.usage.UsageStatsManager
import android.content.Context

object AppUsageTracker {
    fun getAppLaunchCounts(context: Context): Map<String, Int> {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val end = System.currentTimeMillis()
        val start = end - 24 * 60 * 60 * 1000 // Last 24 hours

        val stats = usageStatsManager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, start, end)

        return stats.filter { it.totalTimeInForeground > 0 }
            .associate { it.packageName to it.totalTimeInForeground.toInt() }
    }
}
