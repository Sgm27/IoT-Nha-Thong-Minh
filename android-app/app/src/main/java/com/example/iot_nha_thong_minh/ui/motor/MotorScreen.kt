package com.example.iot_nha_thong_minh.ui.motor

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.RotateLeft
import androidx.compose.material.icons.filled.RotateRight
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.Motor
import com.example.iot_nha_thong_minh.data.model.MotorAction
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun MotorScreen(viewModel: MotorViewModel, modifier: Modifier = Modifier) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Status header
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = if (uiState.isConnected)
                    MaterialTheme.colorScheme.primaryContainer
                else
                    MaterialTheme.colorScheme.errorContainer
            )
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Air,
                    contentDescription = null,
                    modifier = Modifier.size(32.dp),
                    tint = if (uiState.isConnected)
                        MaterialTheme.colorScheme.onPrimaryContainer
                    else
                        MaterialTheme.colorScheme.onErrorContainer
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        text = "Điều khiển Quạt/Động cơ",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = uiState.statusMessage,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }

        // Default fan control if no motors received yet
        if (uiState.motors.isEmpty()) {
            MotorControlCard(
                motor = Motor(
                    name = "Quạt",
                    action = MotorAction.STOP,
                    speed = 0.5f
                ),
                onCommand = { action, speed ->
                    viewModel.sendMotorCommand("Quạt", action, speed)
                }
            )
        }

        // Motor list
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(uiState.motors.values.toList(), key = { it.name }) { motor ->
                MotorControlCard(
                    motor = motor,
                    onCommand = { action, speed ->
                        viewModel.sendMotorCommand(motor.name, action, speed)
                    }
                )
            }
        }
    }
}

@Composable
private fun MotorControlCard(
    motor: Motor,
    onCommand: (MotorAction, Float) -> Unit,
) {
    var sliderSpeed by remember(motor.speed) { mutableFloatStateOf(motor.speed) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (motor.isRunning)
                MaterialTheme.colorScheme.secondaryContainer
            else
                MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header with name and status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = motor.name,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = getStatusText(motor.action),
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (motor.isRunning)
                            MaterialTheme.colorScheme.primary
                        else
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (motor.updatedAtMillis > 0) {
                    Text(
                        text = formatTime(motor.updatedAtMillis),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Speed slider
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "Tốc độ",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = "${(sliderSpeed * 100).toInt()}%",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                Slider(
                    value = sliderSpeed,
                    onValueChange = { sliderSpeed = it },
                    valueRange = 0f..1f,
                    steps = 9
                )
            }

            // Control buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Forward/On button
                ControlButton(
                    modifier = Modifier.weight(1f),
                    icon = Icons.Default.PlayArrow,
                    label = "Bật",
                    isActive = motor.action == MotorAction.ON || motor.action == MotorAction.FORWARD,
                    onClick = { onCommand(MotorAction.ON, sliderSpeed) }
                )

                // Backward button
                ControlButton(
                    modifier = Modifier.weight(1f),
                    icon = Icons.Default.RotateLeft,
                    label = "Nghịch",
                    isActive = motor.action == MotorAction.BACKWARD,
                    onClick = { onCommand(MotorAction.BACKWARD, sliderSpeed) }
                )

                // Stop button
                ControlButton(
                    modifier = Modifier.weight(1f),
                    icon = Icons.Default.Stop,
                    label = "Dừng",
                    isActive = motor.action == MotorAction.STOP || motor.action == MotorAction.OFF,
                    onClick = { onCommand(MotorAction.STOP, sliderSpeed) },
                    isDestructive = true
                )
            }
        }
    }
}

@Composable
private fun ControlButton(
    modifier: Modifier = Modifier,
    icon: ImageVector,
    label: String,
    isActive: Boolean,
    isDestructive: Boolean = false,
    onClick: () -> Unit,
) {
    if (isActive) {
        Button(
            onClick = onClick,
            modifier = modifier,
            colors = if (isDestructive) {
                ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error
                )
            } else {
                ButtonDefaults.buttonColors()
            }
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(text = label)
        }
    } else {
        OutlinedButton(
            onClick = onClick,
            modifier = modifier
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(text = label)
        }
    }
}

private fun getStatusText(action: MotorAction): String = when (action) {
    MotorAction.ON -> "Đang chạy"
    MotorAction.OFF -> "Đã tắt"
    MotorAction.FORWARD -> "Đang quay thuận"
    MotorAction.BACKWARD -> "Đang quay nghịch"
    MotorAction.STOP -> "Đã dừng"
}

private fun formatTime(millis: Long): String {
    val formatter = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    return formatter.format(Date(millis))
}
