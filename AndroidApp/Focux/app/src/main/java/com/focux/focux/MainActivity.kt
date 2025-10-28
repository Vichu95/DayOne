package com.focux.focux

import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.focux.focux.ui.theme.FocuxTheme

class MainActivity : ComponentActivity() {

    private val receiver = ScreenReceiver()
    private var isRegistered = false

    private fun register() {
        if (isRegistered) return
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_USER_PRESENT)
        }
        registerReceiver(receiver, filter)
        isRegistered = true
    }

    private fun unregister() {
        if (!isRegistered) return
        runCatching { unregisterReceiver(receiver) }
        isRegistered = false
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FocuxTheme {
                MaterialTheme { // keep your theme; Material3 is fine
                    Surface(Modifier.fillMaxSize()) {
                        MainScreen(
                            onStart = { register(); LogWriter.append(this, "LISTENING_STARTED") },
                            onStop = { unregister(); LogWriter.append(this, "LISTENING_STOPPED") },
                            onClear = { LogWriter.clear(this) },
                            readLog = { LogWriter.read(this) }
                        )
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        unregister()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainScreen(
    onStart: () -> Unit,
    onStop: () -> Unit,
    onClear: () -> Unit,
    readLog: () -> String,
) {
    var isListening by remember { mutableStateOf(false) }
    var logText by remember { mutableStateOf("") }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Focux — Milestone 1", fontWeight = FontWeight.Bold) }) }
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .padding(16.dp)
                .fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("Goal: Log SCREEN_ON / SCREEN_OFF / UNLOCKED events to a local file.")

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    onClick = {
                        if (!isListening) {
                            onStart()
                            isListening = true
                        }
                    },
                    enabled = !isListening
                ) { Text("Start Listening") }

                OutlinedButton(
                    onClick = {
                        if (isListening) {
                            onStop()
                            isListening = false
                        }
                    },
                    enabled = isListening
                ) { Text("Stop Listening") }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = { logText = readLog() }) { Text("View Log") }
                OutlinedButton(onClick = {
                    onClear()
                    logText = ""
                }) { Text("Clear Log") }
            }

            Divider()
            Text("Log:")
            Text(
                text = if (logText.isBlank()) "(empty)" else logText,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
            )
        }
    }
}
