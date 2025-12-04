package com.example.iot_nha_thong_minh.ui.lights

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.outlined.Lightbulb
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.Light

@Composable
fun LightsScreen(viewModel: LightsViewModel, modifier: Modifier = Modifier) {
    val uiState = viewModel.uiState.collectAsStateWithLifecycle().value
    Column(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (uiState.errorMessage != null) {
            Text(text = uiState.errorMessage, color = MaterialTheme.colorScheme.error)
        }
        if (uiState.isLoading && uiState.lights.isEmpty()) {
            CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
        }

        // Nút bật/tắt tất cả đèn
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = { viewModel.turnOnAllLights() },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(Icons.Filled.Lightbulb, contentDescription = null)
                Text("Bật tất cả", modifier = Modifier.padding(start = 8.dp))
            }
            OutlinedButton(
                onClick = { viewModel.turnOffAllLights() },
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Outlined.Lightbulb, contentDescription = null)
                Text("Tắt tất cả", modifier = Modifier.padding(start = 8.dp))
            }
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(uiState.lights, key = { it.location }) { light ->
                LightItem(light = light, onToggle = { viewModel.toggleLight(light) })
            }
        }
    }
}

@Composable
private fun LightItem(light: Light, onToggle: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column {
                Text(text = light.location, style = MaterialTheme.typography.titleMedium)
                Text(
                    text = if (light.isOn) "Đang bật" else "Đang tắt",
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (light.isOn) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Switch(checked = light.isOn, onCheckedChange = { onToggle() })
        }
    }
}
