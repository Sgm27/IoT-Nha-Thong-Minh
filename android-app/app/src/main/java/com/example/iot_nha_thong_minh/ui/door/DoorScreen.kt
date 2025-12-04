package com.example.iot_nha_thong_minh.ui.door

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DoorBack
import androidx.compose.material.icons.filled.DoorFront
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.Door

@Composable
fun DoorScreen(viewModel: DoorViewModel, modifier: Modifier = Modifier) {
    val uiState = viewModel.uiState.collectAsStateWithLifecycle().value
    Column(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (uiState.errorMessage != null) {
            Text(text = uiState.errorMessage, color = MaterialTheme.colorScheme.error)
        }
        if (uiState.isLoading && uiState.doors.isEmpty()) {
            CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(uiState.doors, key = { it.location }) { door ->
                DoorItem(
                    door = door,
                    onOpen = { viewModel.openDoor(door) },
                    onClose = { viewModel.closeDoor(door) }
                )
            }
        }
    }
}

@Composable
private fun DoorItem(door: Door, onOpen: () -> Unit, onClose: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Tiêu đề và trạng thái
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(text = door.location, style = MaterialTheme.typography.titleMedium)
                    Text(
                        text = if (door.isOpen) "Đang mở (${door.angle.toInt()}°)" else "Đang đóng",
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (door.isOpen) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            // Nút điều khiển
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onOpen,
                    modifier = Modifier.weight(1f),
                    enabled = !door.isOpen,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                ) {
                    Icon(Icons.Filled.DoorFront, contentDescription = null)
                    Text("Mở cửa", modifier = Modifier.padding(start = 8.dp))
                }
                OutlinedButton(
                    onClick = onClose,
                    modifier = Modifier.weight(1f),
                    enabled = door.isOpen
                ) {
                    Icon(Icons.Filled.DoorBack, contentDescription = null)
                    Text("Đóng cửa", modifier = Modifier.padding(start = 8.dp))
                }
            }
        }
    }
}
