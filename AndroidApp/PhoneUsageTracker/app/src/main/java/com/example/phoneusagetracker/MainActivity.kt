package com.example.phoneusagetracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.phoneusagetracker.ui.theme.PhoneUsageTrackerTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PhoneUsageTrackerTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    UsageStatsScreen()
                }
            }
        }
    }
}

@Composable
fun UsageStatsScreen() {
    var touchCount by remember { mutableStateOf(0) }
    var swipeCount by remember { mutableStateOf(0) }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("Touch Count: $touchCount")
        Text("Swipe Count: $swipeCount")
    }
}
