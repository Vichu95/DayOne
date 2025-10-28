package com.example.phoneusagetracker

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent

class MyAccessibilityService : AccessibilityService() {

    companion object {
        var touchCount = 0
        var swipeCount = 0
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        when (event?.eventType) {
            AccessibilityEvent.TYPE_VIEW_CLICKED -> {
                touchCount++
            }
            AccessibilityEvent.TYPE_VIEW_SCROLLED -> {
                swipeCount++
            }
        }
    }

    override fun onInterrupt() {}
}
