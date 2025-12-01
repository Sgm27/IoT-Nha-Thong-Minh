package com.example.iot_nha_thong_minh.ui.fire

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.LocalFireDepartment
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.FireAlert
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun FireScreen(viewModel: FireViewModel, modifier: Modifier = Modifier) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
        ) {
            // Status header
            StatusHeader(
                isConnected = uiState.isConnected,
                statusMessage = uiState.statusMessage,
                unacknowledgedCount = uiState.unacknowledgedCount,
                onAcknowledgeAll = { viewModel.acknowledgeAllAlerts() },
                onClearHistory = { viewModel.clearHistory() }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Alert history
            if (uiState.alerts.isEmpty()) {
                EmptyState()
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(uiState.alerts, key = { it.id }) { alert ->
                        AlertCard(
                            alert = alert,
                            onAcknowledge = { viewModel.acknowledgeAlert(alert.id) }
                        )
                    }
                }
            }
        }

        // Latest alert overlay
        AnimatedVisibility(
            visible = uiState.latestAlert != null,
            enter = slideInVertically { -it } + fadeIn(),
            exit = slideOutVertically { -it } + fadeOut(),
            modifier = Modifier.align(Alignment.TopCenter)
        ) {
            uiState.latestAlert?.let { alert ->
                LatestAlertBanner(
                    alert = alert,
                    onDismiss = { viewModel.dismissLatestAlert() }
                )
            }
        }
    }
}

@Composable
private fun StatusHeader(
    isConnected: Boolean,
    statusMessage: String,
    unacknowledgedCount: Int,
    onAcknowledgeAll: () -> Unit,
    onClearHistory: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (unacknowledgedCount > 0)
                MaterialTheme.colorScheme.errorContainer
            else if (isConnected)
                MaterialTheme.colorScheme.primaryContainer
            else
                MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = if (unacknowledgedCount > 0)
                        Icons.Default.Warning
                    else
                        Icons.Default.LocalFireDepartment,
                    contentDescription = null,
                    modifier = Modifier.size(32.dp),
                    tint = if (unacknowledgedCount > 0)
                        MaterialTheme.colorScheme.error
                    else if (isConnected)
                        MaterialTheme.colorScheme.onPrimaryContainer
                    else
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = if (unacknowledgedCount > 0)
                            "$unacknowledgedCount cảnh báo chưa xác nhận"
                        else
                            "Phát hiện cháy",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = statusMessage,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }

            if (unacknowledgedCount > 0) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = onAcknowledgeAll,
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Xác nhận tất cả")
                    }
                    OutlinedButton(
                        onClick = onClearHistory,
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Delete,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Xóa lịch sử")
                    }
                }
            }
        }
    }
}

@Composable
private fun EmptyState() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.6f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "Không có cảnh báo",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = "Hệ thống đang giám sát và phát hiện cháy.\nCác cảnh báo sẽ hiển thị tại đây.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun AlertCard(
    alert: FireAlert,
    onAcknowledge: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (alert.isAcknowledged)
                MaterialTheme.colorScheme.surfaceVariant
            else
                MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.7f)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Fire icon
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(
                            if (alert.isAcknowledged)
                                MaterialTheme.colorScheme.outline.copy(alpha = 0.3f)
                            else
                                MaterialTheme.colorScheme.error
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.LocalFireDepartment,
                        contentDescription = null,
                        tint = if (alert.isAcknowledged)
                            MaterialTheme.colorScheme.onSurfaceVariant
                        else
                            MaterialTheme.colorScheme.onError,
                        modifier = Modifier.size(24.dp)
                    )
                }

                Spacer(modifier = Modifier.width(12.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = alert.message,
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = if (alert.isAcknowledged) FontWeight.Normal else FontWeight.Bold
                    )
                    Text(
                        text = formatTimestamp(alert.timestampMillis),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                if (!alert.isAcknowledged) {
                    IconButton(onClick = onAcknowledge) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = "Xác nhận",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }

            // Detection details
            if (alert.confidence != null || alert.fireRegions != null || alert.firePercentage != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    alert.confidence?.let { confidence ->
                        DetailChip(
                            label = "Độ tin cậy",
                            value = String.format(Locale.US, "%.1f%%", confidence)
                        )
                    }
                    alert.fireRegions?.let { regions ->
                        DetailChip(
                            label = "Vùng lửa",
                            value = regions.toString()
                        )
                    }
                    alert.firePercentage?.let { percentage ->
                        DetailChip(
                            label = "Diện tích",
                            value = String.format(Locale.US, "%.2f%%", percentage)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun DetailChip(label: String, value: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun LatestAlertBanner(
    alert: FireAlert,
    onDismiss: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.error
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.Warning,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onError,
                modifier = Modifier.size(32.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "CẢNH BÁO CHÁY!",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onError
                )
                Text(
                    text = alert.message,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onError.copy(alpha = 0.9f)
                )
            }
            IconButton(onClick = onDismiss) {
                Icon(
                    imageVector = Icons.Default.Clear,
                    contentDescription = "Đóng",
                    tint = MaterialTheme.colorScheme.onError
                )
            }
        }
    }
}

private fun formatTimestamp(millis: Long): String {
    val formatter = SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.getDefault())
    return formatter.format(Date(millis))
}
